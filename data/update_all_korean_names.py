#!/usr/bin/env python3
"""
구글 검색으로 모든 캐릭터의 공식 한국어 이름 업데이트
- 기존 한국어 이름도 전부 재검증
- 구글 rate limit 우회 (여러 브라우저 프로필, 랜덤 딜레이)
- 최대 속도로 병렬 처리

예: "Eren Yeager" 이름 → 엘런 예거
"""
import sys
import os
import re
import json
import asyncio
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: pip install playwright && playwright install chromium")
    sys.exit(1)


# ============================================================
# Configuration - 구글 rate limit 우회 최적화
# ============================================================
MAX_WORKERS = 5  # 브라우저 5개 동시 실행
MIN_DELAY = 2.0  # 최소 딜레이 (초)
MAX_DELAY = 4.0  # 최대 딜레이 (초) - 랜덤화로 봇 감지 회피
PAGE_TIMEOUT = 12000
MAX_CHARACTERS = None  # None = 전체, 숫자로 제한 가능

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_all_korean_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_all_korean_errors.log"

# Global counters
processed_count = 0
success_count = 0
updated_count = 0
lock = asyncio.Lock()

# User Agent Pool - 다양한 브라우저 시뮬레이션
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def log_error(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"processed_ids": [], "updated": {}, "same": [], "not_found": [], "errors": []}


def save_progress(progress):
    try:
        # 너무 커지지 않도록 same, not_found는 ID만 저장
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False)
    except Exception as e:
        log_error(f"Failed to save progress: {e}")


def get_all_characters(limit=None, exclude_ids=None):
    """모든 캐릭터 조회 (한국어 이름 있는 것 포함)"""
    exclude_ids = exclude_ids or []

    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.name_korean,
            c.favourites
        FROM character c
        WHERE c.name_native IS NOT NULL
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra')
          AND c.name_native != ''
          AND LENGTH(c.name_native) >= 2
          AND LENGTH(c.name_full) >= 3
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


def is_valid_korean_name(text):
    """유효한 한국어 이름인지 확인"""
    if not text:
        return False
    text = text.strip()
    # 한글만 (공백 허용)
    if not re.match(r'^[가-힣]+(\s[가-힣]+)*$', text):
        return False
    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 15:
        return False
    # 블랙리스트 - 검색 결과에서 흔히 나오는 단어들
    blacklist = ['이름', '목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
                 '검색', '결과', '나무위키', '위키백과', '더보기', '관련', '문서',
                 '애니메이션', '만화', '게임', '소설', '작품', '시리즈', '캐릭터',
                 '공식', '정보', '프로필', '소개', '한국어', '일본어', '영어',
                 '번역', '발음', '표기', '원문']
    if text in blacklist or any(b == text for b in blacklist):
        return False
    return True


def extract_korean_name_from_google(page_text, name_full):
    """구글 검색 결과에서 한국어 이름 추출"""
    lines = page_text.split('\n')
    korean_names = []
    first_name = name_full.split()[0] if ' ' in name_full else name_full

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 패턴 1: "한국어이름 - 나무위키" 형태
        match = re.search(r'^([가-힣]{2,10}(?:\s[가-힣]{1,10})?)\s*[-–—]\s*나무위키', line)
        if match:
            name = match.group(1).strip()
            if is_valid_korean_name(name):
                korean_names.append(name)
                continue

        # 패턴 2: "한국어이름(영어이름)" 형태
        match = re.search(r'^([가-힣]{2,10}(?:\s[가-힣]{1,10})?)\s*[\(（]', line)
        if match:
            # 영어 이름이 포함되어 있는지 확인
            if first_name.lower() in line.lower():
                name = match.group(1).strip()
                if is_valid_korean_name(name):
                    korean_names.append(name)
                    continue

        # 패턴 3: 나무위키 URL에서 추출 (/w/한국어이름)
        match = re.search(r'namu\.wiki/w/([가-힣%]+(?:%20[가-힣%]+)*)', line)
        if match:
            try:
                name = unquote(match.group(1))
                # 괄호 제거 (동명이인 구분용)
                name = re.sub(r'[\(（].*?[\)）]$', '', name).strip()
                if is_valid_korean_name(name):
                    korean_names.append(name)
            except:
                pass

        # 패턴 4: 위키백과 제목
        match = re.search(r'^([가-힣]{2,10}(?:\s[가-힣]{1,10})?)\s*[-–—]\s*위키', line)
        if match:
            name = match.group(1).strip()
            if is_valid_korean_name(name):
                korean_names.append(name)

    # 가장 많이 나온 이름 반환 (신뢰도 높음)
    if korean_names:
        from collections import Counter
        counter = Counter(korean_names)
        most_common_name, count = counter.most_common(1)[0]
        # 최소 1번 이상 나와야 함
        if count >= 1:
            return most_common_name

    return None


async def search_google_with_retry(page, name_full, max_retries=2):
    """구글 검색 (재시도 포함)"""
    search_query = f'"{name_full}" 이름'

    for attempt in range(max_retries):
        try:
            await page.goto(
                f"https://www.google.com/search?q={search_query}&hl=ko&gl=kr",
                timeout=PAGE_TIMEOUT,
                wait_until='domcontentloaded'
            )

            # 봇 감지 체크
            content = await page.content()
            if 'unusual traffic' in content.lower() or 'captcha' in content.lower():
                log_error(f"Bot detection for {name_full}, attempt {attempt + 1}")
                await asyncio.sleep(30)  # 30초 대기 후 재시도
                continue

            await asyncio.sleep(0.5)

            page_text = await page.evaluate("document.body.innerText")
            korean_name = extract_korean_name_from_google(page_text, name_full)

            return korean_name

        except PlaywrightTimeout:
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            log_error(f"Timeout for {name_full}")
            return None
        except Exception as e:
            log_error(f"Error for {name_full}: {e}")
            return None

    return None


async def worker(worker_id, queue, playwright, total_count, progress):
    """Worker - 구글 검색 수행"""
    global processed_count, success_count, updated_count

    browser = None
    context = None
    page = None

    try:
        # 랜덤 User Agent 선택
        user_agent = USER_AGENTS[worker_id % len(USER_AGENTS)]

        browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']  # 봇 감지 우회
        )
        context = await browser.new_context(
            user_agent=user_agent,
            locale='ko-KR',
            viewport={'width': 1920, 'height': 1080}
        )

        # 봇 감지 우회를 위한 추가 설정
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()
        log(f"Worker {worker_id}: 시작")

        consecutive_failures = 0
        max_consecutive_failures = 5

        while True:
            try:
                character = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            char_id = character['id']
            name_full = character['name_full']
            name_native = character['name_native']
            current_korean = character['name_korean']

            # 구글 검색
            found_korean = await search_google_with_retry(page, name_full)

            async with lock:
                processed_count += 1
                current = processed_count

                if found_korean:
                    success_count += 1
                    consecutive_failures = 0

                    if current_korean != found_korean:
                        # 업데이트 필요
                        db.execute_update(
                            "UPDATE character SET name_korean = ? WHERE id = ?",
                            (found_korean, char_id)
                        )
                        updated_count += 1
                        progress["updated"][str(char_id)] = {
                            "name": name_full,
                            "old": current_korean,
                            "new": found_korean
                        }
                        log(f"✓ [{current}/{total_count}] {name_full}: {current_korean or '없음'} → {found_korean}")
                    else:
                        progress["same"].append(char_id)
                        # 동일한 경우 로그 생략 (너무 많음)
                else:
                    consecutive_failures += 1
                    progress["not_found"].append(char_id)

                progress["processed_ids"].append(char_id)

                # 50개마다 진행상황 출력 및 저장
                if current % 50 == 0:
                    rate = success_count / current * 100 if current > 0 else 0
                    log(f"\n{'='*50}")
                    log(f"📊 진행: {current}/{total_count} ({current/total_count*100:.1f}%)")
                    log(f"   찾음: {success_count}개 ({rate:.1f}%)")
                    log(f"   업데이트: {updated_count}개")
                    log(f"{'='*50}\n")
                    save_progress(progress)

            # 연속 실패 시 브라우저 재시작
            if consecutive_failures >= max_consecutive_failures:
                log(f"Worker {worker_id}: 연속 실패 {consecutive_failures}회, 브라우저 재시작...")
                try:
                    await page.close()
                    await context.close()
                    await browser.close()
                except:
                    pass

                await asyncio.sleep(10)

                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    locale='ko-KR'
                )
                page = await context.new_page()
                consecutive_failures = 0

            # 랜덤 딜레이 (봇 감지 우회)
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

    except Exception as e:
        log_error(f"Worker {worker_id} fatal error: {e}")

    finally:
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
    global processed_count, success_count, updated_count

    log("=" * 60)
    log("🔍 구글 검색으로 모든 캐릭터 한국어 이름 업데이트")
    log(f"   Worker: {MAX_WORKERS}개")
    log(f"   딜레이: {MIN_DELAY}~{MAX_DELAY}초 (랜덤)")
    log("=" * 60)

    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행 상황:")
        log(f"   처리됨: {len(processed_ids)}개")
        log(f"   업데이트: {len(progress.get('updated', {}))}개")
        log(f"   동일: {len(progress.get('same', []))}개")
        log(f"   못찾음: {len(progress.get('not_found', []))}개")

    log("\n📋 캐릭터 조회 중...")
    characters = get_all_characters(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0
    updated_count = 0

    queue = asyncio.Queue()
    for char in characters:
        await queue.put(char)

    log(f"\n🔄 검색 시작...")
    log(f"   예상 시간: {total_count * (MIN_DELAY + MAX_DELAY) / 2 / MAX_WORKERS / 60:.0f}분")
    start_time = datetime.now()

    async with async_playwright() as p:
        workers_tasks = [
            worker(i, queue, p, total_count, progress)
            for i in range(MAX_WORKERS)
        ]
        await asyncio.gather(*workers_tasks)

    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n{'='*60}")
    log("🎉 완료!")
    log(f"  처리: {processed_count}개")
    log(f"  찾음: {success_count}개 ({success_count/max(processed_count,1)*100:.1f}%)")
    log(f"  업데이트: {updated_count}개")
    log(f"  시간: {elapsed/60:.1f}분")
    log(f"  속도: {processed_count/max(elapsed,1)*60:.1f}개/분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
