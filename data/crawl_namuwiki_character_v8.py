#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v8
안정성 개선 버전:
- 에러 로깅 및 재시도
- Worker별 독립 브라우저
- 진행 상황 JSON 저장 (중단 후 재개 가능)
- 페이지 충돌 시 자동 복구
- Rate limiting 대응
"""
import sys
import os
import re
import json
import asyncio
import traceback
from urllib.parse import quote, unquote
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright not installed")
    sys.exit(1)


# Configuration
MAX_WORKERS = 3  # 5 -> 3으로 줄여서 안정성 향상
MAX_CHARACTERS = None  # None = 전체
REQUEST_DELAY = 1.0  # 0.5 -> 1.0으로 늘림
PAGE_TIMEOUT = 20000  # 페이지 로딩 타임아웃 (20초)
MAX_RETRIES = 3  # 재시도 횟수

# 진행 상황 파일
PROGRESS_FILE = Path(__file__).parent / "crawl_progress_v8.json"
ERROR_LOG_FILE = Path(__file__).parent / "crawl_errors_v8.log"

# Global counters
processed_count = 0
success_count = 0
error_count = 0
lock = asyncio.Lock()


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def log_error(msg, error=None):
    """에러를 파일에 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
        if error:
            f.write(f"    {traceback.format_exc()}\n")


def load_progress():
    """이전 진행 상황 로드"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"processed_ids": [], "success": {}, "failed": []}


def save_progress(progress):
    """진행 상황 저장"""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"Failed to save progress: {e}")


def get_characters_to_crawl(limit=None, exclude_ids=None):
    """크롤링할 캐릭터 조회 (이미 처리한 것 제외)"""
    exclude_ids = exclude_ids or []

    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.favourites
        FROM character c
        WHERE c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra')
          AND c.name_native != ''
          AND LENGTH(c.name_native) >= 2
    """

    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        query += f" AND c.id NOT IN ({placeholders})"

    query += " ORDER BY c.favourites DESC"

    if limit:
        query += f" LIMIT {limit}"

    if exclude_ids:
        return db.execute_query(query, tuple(exclude_ids))
    return db.execute_query(query)


def extract_kanji(text):
    """한자만 추출"""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def is_valid_korean_name(text):
    if not text:
        return False
    text = text.strip()
    if not re.match(r'^[가-힣]+(\s[가-힣]+)?$', text):
        return False
    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 10:
        return False
    blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '편집', '토론', '역사', '최근', '수정', '시각', '기능',
                 '작품', '시리즈', '애니', '만화', '게임', '소설', '더보기',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록']
    if text in blacklist or any(b in text for b in blacklist):
        return False
    return True


def is_character_document(page_text):
    """캐릭터 문서인지 확인"""
    header = page_text[:4000]

    # 분류 확인
    category_line = ""
    for line in header.split('\n')[:15]:
        if '분류' in line:
            category_line = line
            break

    # 실존 인물 카테고리 제외
    real_person_cats = ['남배우', '여배우', '가수', '아이돌',
                        '출생', '데뷔', '출신 인물', '소속 연예인']
    for cat in real_person_cats:
        if cat in category_line:
            return False

    # 직업이 배우인 경우 제외
    lines = header.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '직업':
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.search(r'배우\s*\(\d{4}', next_line):
                    return False

    # 성우 정보 필수
    if '성우' not in header:
        return False

    return True


def match_infobox_name(page_text, target_native, target_english):
    """인포박스에서 일본어+영어 이름 엄격 매칭"""
    target_kanji = extract_kanji(target_native)

    if len(target_kanji) < 2:
        target_kanji = target_native

    english_full = target_english.lower().replace(' ', '')
    lines = page_text.split('\n')[:80]

    for line in lines:
        if ('/' in line or '｜' in line or '|' in line) and re.search(r'[A-Za-z]', line):
            line_kanji = extract_kanji(line)

            if not line_kanji or target_kanji != line_kanji:
                continue

            line_english = ''.join(re.findall(r'[A-Za-z]+', line)).lower()

            if english_full and line_english:
                common = sum(1 for c in english_full if c in line_english)
                if common >= len(english_full) * 0.7:
                    return True

            return True

    return False


def extract_korean_title(page_text):
    """페이지 상단에서 한글 제목 추출"""
    lines = page_text.split('\n')
    for line in lines[:20]:
        line = line.strip()
        if is_valid_korean_name(line):
            return line
    return None


async def safe_goto(page, url, timeout=PAGE_TIMEOUT):
    """안전한 페이지 이동 (재시도 포함)"""
    for attempt in range(MAX_RETRIES):
        try:
            await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            return True
        except PlaywrightTimeout:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2)
                continue
            return False
        except Exception as e:
            log_error(f"Navigation error to {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2)
                continue
            return False
    return False


async def search_and_find(page, search_term, name_native, name_full):
    """검색 후 캐릭터 찾기"""
    search_url = f"https://namu.wiki/Search?q={quote(search_term)}"

    if not await safe_goto(page, search_url):
        return None

    await asyncio.sleep(0.5)

    try:
        # 검색 결과에서 URL 추출
        results = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();
                document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href.includes('#') || href.includes(':')) return;
                    if (seen.has(href)) return;
                    seen.add(href);
                    items.push(href);
                });
                return items.slice(0, 30);
            }
        """)

        # 한글 이름 URL만
        korean_candidates = []
        for href in results:
            try:
                decoded = unquote(href.replace('/w/', ''))
                name_part = re.sub(r'\([^)]*\)$', '', decoded).strip()
                if is_valid_korean_name(name_part):
                    korean_candidates.append({'name': name_part, 'href': href})
            except:
                pass

        # 중복 제거
        seen = set()
        unique = []
        for c in korean_candidates:
            if c['name'] not in seen:
                seen.add(c['name'])
                unique.append(c)

        # 각 후보 확인
        for candidate in unique[:8]:
            korean_name = candidate['name']
            href = candidate['href']

            doc_url = f"https://namu.wiki{href}"

            if not await safe_goto(page, doc_url, timeout=15000):
                continue

            await asyncio.sleep(0.3)

            try:
                page_text = await page.evaluate("document.body.innerText")

                if "해당 문서를 찾을 수 없습니다" in page_text:
                    continue

                if not is_character_document(page_text):
                    continue

                if match_infobox_name(page_text, name_native, name_full):
                    title = extract_korean_title(page_text)
                    if title:
                        return title
                    return korean_name

            except Exception as e:
                log_error(f"Error processing {doc_url}: {e}")
                continue

            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        log_error(f"Search error for {search_term}: {e}")

    return None


async def find_korean_name(page, name_native, name_full):
    """나무위키에서 한국어 이름 찾기 (다중 검색)"""

    # 1. 일본어 이름으로 검색
    result = await search_and_find(page, name_native, name_native, name_full)
    if result:
        return result

    # 2. 영어 이름으로 검색
    result = await search_and_find(page, name_full, name_native, name_full)
    if result:
        return result

    # 3. 영어 이름 일부로 검색 (성만)
    parts = name_full.split()
    if len(parts) >= 2:
        result = await search_and_find(page, parts[-1], name_native, name_full)
        if result:
            return result

    return None


async def create_browser_and_page(playwright):
    """새 브라우저와 페이지 생성"""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = await context.new_page()
    return browser, context, page


async def worker(worker_id, queue, playwright, total_count, progress):
    """개선된 Worker - 독립 브라우저, 자동 복구"""
    global processed_count, success_count, error_count

    browser = None
    context = None
    page = None

    consecutive_errors = 0
    max_consecutive_errors = 5

    try:
        browser, context, page = await create_browser_and_page(playwright)
        log(f"Worker {worker_id}: 시작")

        while True:
            try:
                character = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            char_id = character['id']
            name_full = character['name_full']
            name_native = character['name_native']

            korean_name = None
            error_occurred = False

            try:
                korean_name = await find_korean_name(page, name_native, name_full)

                if korean_name:
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (korean_name, char_id)
                    )
                    consecutive_errors = 0
                else:
                    consecutive_errors = 0  # 실패해도 에러는 아님

            except Exception as e:
                error_occurred = True
                consecutive_errors += 1
                log_error(f"Worker {worker_id} error on {name_full}: {e}", e)

                # 연속 에러가 많으면 브라우저 재시작
                if consecutive_errors >= max_consecutive_errors:
                    log(f"Worker {worker_id}: 연속 에러 {consecutive_errors}회, 브라우저 재시작...")
                    try:
                        await page.close()
                        await context.close()
                        await browser.close()
                    except:
                        pass

                    await asyncio.sleep(3)
                    browser, context, page = await create_browser_and_page(playwright)
                    consecutive_errors = 0

            # 진행 상황 업데이트
            async with lock:
                processed_count += 1
                current = processed_count

                if korean_name:
                    success_count += 1
                    progress["success"][str(char_id)] = korean_name
                    log(f"✓ [{current}/{total_count}] {name_full} ({name_native}) → {korean_name}")
                elif error_occurred:
                    error_count += 1
                    progress["failed"].append(char_id)
                    log(f"⚠ [{current}/{total_count}] {name_full} (에러)")
                else:
                    log(f"✗ [{current}/{total_count}] {name_full}")

                progress["processed_ids"].append(char_id)

                # 10개마다 진행상황 출력 및 저장
                if current % 10 == 0:
                    rate = success_count / current * 100 if current > 0 else 0
                    log(f"\n{'='*60}")
                    log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
                    log(f"   성공: {success_count}개 ({rate:.1f}%)")
                    log(f"   실패: {current - success_count - error_count}개")
                    log(f"   에러: {error_count}개")
                    log(f"{'='*60}\n")

                    # 진행 상황 저장
                    save_progress(progress)

            # Rate limiting 대응
            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        log_error(f"Worker {worker_id} fatal error: {e}", e)

    finally:
        # 정리
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
        except:
            pass

        log(f"Worker {worker_id}: 종료")


async def main():
    global processed_count, success_count, error_count

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v8")
    log(f"   안정성 개선 + {MAX_WORKERS}개 독립 Worker")
    log("=" * 60)

    # 이전 진행 상황 로드
    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행 상황 발견: {len(processed_ids)}개 처리됨")
        log(f"   성공: {len(progress.get('success', {}))}개")
        log(f"   이어서 진행합니다...\n")

    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 발견")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0
    error_count = 0

    queue = asyncio.Queue()
    for char in characters:
        await queue.put(char)

    log(f"\n🔄 크롤링 시작 ({MAX_WORKERS}개 Worker)...")
    start_time = datetime.now()

    async with async_playwright() as p:
        workers = [
            worker(i, queue, p, total_count, progress)
            for i in range(MAX_WORKERS)
        ]

        await asyncio.gather(*workers)

    # 최종 진행 상황 저장
    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n\n{'='*60}")
    log("🎉 크롤링 완료!")
    log(f"{'='*60}")
    log(f"  총 처리: {processed_count}개")
    if processed_count > 0:
        log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
        log(f"  실패: {processed_count - success_count - error_count}개")
        log(f"  에러: {error_count}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"  진행 상황 저장: {PROGRESS_FILE}")
    log(f"  에러 로그: {ERROR_LOG_FILE}")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
