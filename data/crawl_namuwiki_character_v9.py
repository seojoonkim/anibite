#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v9
초고속 버전 - httpx 사용 (Playwright 대비 10배 이상 빠름)

- 브라우저 없이 HTTP 요청만 사용
- 20개 동시 요청
- 진행 상황 저장 (중단 후 재개 가능)
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
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: httpx와 beautifulsoup4가 필요합니다")
    print("pip install httpx beautifulsoup4")
    sys.exit(1)


# Configuration
MAX_CONCURRENT = 15  # 동시 요청 수
MAX_CHARACTERS = None  # None = 전체
REQUEST_TIMEOUT = 10  # 초
MAX_RETRIES = 2

# 진행 상황 파일
PROGRESS_FILE = Path(__file__).parent / "crawl_progress_v9.json"
ERROR_LOG_FILE = Path(__file__).parent / "crawl_errors_v9.log"

# Global counters
processed_count = 0
success_count = 0
error_count = 0
lock = asyncio.Lock()

# Rate limiting
semaphore = None


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def log_error(msg, error=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
        if error:
            f.write(f"    {error}\n")


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"processed_ids": [], "success": {}, "failed": []}


def save_progress(progress):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"Failed to save progress: {e}")


def get_characters_to_crawl(limit=None, exclude_ids=None):
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


def is_character_document(text):
    header = text[:4000]

    category_line = ""
    for line in header.split('\n')[:15]:
        if '분류' in line:
            category_line = line
            break

    real_person_cats = ['남배우', '여배우', '가수', '아이돌',
                        '출생', '데뷔', '출신 인물', '소속 연예인']
    for cat in real_person_cats:
        if cat in category_line:
            return False

    lines = header.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '직업':
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.search(r'배우\s*\(\d{4}', next_line):
                    return False

    if '성우' not in header:
        return False

    return True


def match_infobox_name(text, target_native, target_english):
    target_kanji = extract_kanji(target_native)

    if len(target_kanji) < 2:
        target_kanji = target_native

    english_full = target_english.lower().replace(' ', '')
    lines = text.split('\n')[:80]

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


def extract_korean_title(text):
    lines = text.split('\n')
    for line in lines[:20]:
        line = line.strip()
        if is_valid_korean_name(line):
            return line
    return None


async def fetch_page(client, url):
    """페이지 가져오기 (재시도 포함)"""
    for attempt in range(MAX_RETRIES):
        try:
            async with semaphore:
                response = await client.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    # Rate limited - 잠시 대기
                    await asyncio.sleep(2)
                    continue
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)
                continue
    return None


def extract_text_from_html(html):
    """HTML에서 텍스트 추출"""
    soup = BeautifulSoup(html, 'html.parser')

    # 불필요한 태그 제거
    for tag in soup(['script', 'style', 'nav', 'footer']):
        tag.decompose()

    return soup.get_text(separator='\n', strip=True)


def extract_links_from_search(html):
    """검색 결과에서 링크 추출"""
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/w/') and '#' not in href and ':' not in href:
            links.append(href)

    return list(dict.fromkeys(links))[:30]  # 중복 제거, 상위 30개


async def search_and_find(client, search_term, name_native, name_full):
    """검색 후 캐릭터 찾기"""
    search_url = f"https://namu.wiki/Search?q={quote(search_term)}"

    html = await fetch_page(client, search_url)
    if not html:
        return None

    links = extract_links_from_search(html)

    # 한글 이름 URL만 필터링
    korean_candidates = []
    for href in links:
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

    # 각 후보 확인 (상위 5개만)
    for candidate in unique[:5]:
        korean_name = candidate['name']
        href = candidate['href']

        doc_url = f"https://namu.wiki{href}"
        doc_html = await fetch_page(client, doc_url)

        if not doc_html:
            continue

        text = extract_text_from_html(doc_html)

        if "해당 문서를 찾을 수 없습니다" in text:
            continue

        if not is_character_document(text):
            continue

        if match_infobox_name(text, name_native, name_full):
            title = extract_korean_title(text)
            if title:
                return title
            return korean_name

    return None


async def find_korean_name(client, name_native, name_full):
    """나무위키에서 한국어 이름 찾기"""

    # 1. 일본어 이름으로 검색
    result = await search_and_find(client, name_native, name_native, name_full)
    if result:
        return result

    # 2. 영어 이름으로 검색
    result = await search_and_find(client, name_full, name_native, name_full)
    if result:
        return result

    # 3. 영어 이름 일부로 검색 (성만)
    parts = name_full.split()
    if len(parts) >= 2:
        result = await search_and_find(client, parts[-1], name_native, name_full)
        if result:
            return result

    return None


async def process_character(client, character, total_count, progress):
    """단일 캐릭터 처리"""
    global processed_count, success_count, error_count

    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']

    korean_name = None
    error_occurred = False

    try:
        korean_name = await find_korean_name(client, name_native, name_full)

        if korean_name:
            db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (korean_name, char_id)
            )

    except Exception as e:
        error_occurred = True
        log_error(f"Error on {name_full}: {e}")

    # 진행 상황 업데이트
    async with lock:
        processed_count += 1
        current = processed_count

        if korean_name:
            success_count += 1
            progress["success"][str(char_id)] = korean_name
            log(f"✓ [{current}/{total_count}] {name_full} → {korean_name}")
        elif error_occurred:
            error_count += 1
            progress["failed"].append(char_id)
            log(f"⚠ [{current}/{total_count}] {name_full} (에러)")
        else:
            log(f"✗ [{current}/{total_count}] {name_full}")

        progress["processed_ids"].append(char_id)

        # 50개마다 진행상황 저장
        if current % 50 == 0:
            rate = success_count / current * 100 if current > 0 else 0
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
            log(f"   성공: {success_count}개 ({rate:.1f}%)")
            log(f"   실패: {current - success_count - error_count}개")
            log(f"   에러: {error_count}개")
            log(f"{'='*60}\n")
            save_progress(progress)


async def main():
    global processed_count, success_count, error_count, semaphore

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v9")
    log(f"   초고속 httpx 버전 - {MAX_CONCURRENT}개 동시 요청")
    log("=" * 60)

    # Semaphore 초기화
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

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

    log(f"\n🔄 크롤링 시작...")
    start_time = datetime.now()

    # HTTP 클라이언트 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # 배치로 처리 (메모리 관리)
        batch_size = 100
        for i in range(0, len(characters), batch_size):
            batch = characters[i:i + batch_size]

            tasks = [
                process_character(client, char, total_count, progress)
                for char in batch
            ]

            await asyncio.gather(*tasks)

            # 배치 완료 후 잠시 대기 (rate limiting)
            await asyncio.sleep(1)

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
    log(f"  속도: {processed_count / elapsed * 60:.1f}개/분")
    log(f"  진행 상황 저장: {PROGRESS_FILE}")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
