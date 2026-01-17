#!/usr/bin/env python3
"""
구글 검색으로 공식 한국어 이름 찾기 및 업데이트
Playwright 기반 - 봇 차단 우회

검색 쿼리: "캐릭터 영어이름" 이름
예: "Eren Yeager" 이름 → 엘런 예거
"""
import sys
import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: pip install playwright && playwright install chromium")
    sys.exit(1)


# Configuration
MAX_WORKERS = 2  # 구글은 봇 감지가 빡세서 적게
MAX_CHARACTERS = None  # None = 전체
REQUEST_DELAY = 3.0  # 구글 rate limit 대응
PAGE_TIMEOUT = 15000

PROGRESS_FILE = Path(__file__).parent / "update_korean_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_korean_errors.log"

# Global
processed_count = 0
success_count = 0
updated_count = 0
lock = asyncio.Lock()


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
    return {"processed_ids": [], "updated": {}, "same": [], "not_found": []}


def save_progress(progress):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except:
        pass


def get_characters_to_update(limit=None, exclude_ids=None):
    """인기 캐릭터 조회 (한국어 이름 있는 것 포함)"""
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
          AND c.favourites >= 100
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
    # 블랙리스트
    blacklist = ['이름', '목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
                 '검색', '결과', '나무위키', '위키백과', '더보기', '관련', '문서']
    if text in blacklist or any(b in text for b in blacklist):
        return False
    return True


def extract_korean_name_from_google(page_text, name_full):
    """구글 검색 결과에서 한국어 이름 추출"""
    lines = page_text.split('\n')

    korean_names = []

    for line in lines:
        line = line.strip()

        # 패턴 1: "한국어이름(영어이름)" 또는 "한국어이름 - "
        # 예: "엘런 예거(Eren Yeager)" 또는 "엘런 예거 - 나무위키"
        patterns = [
            r'([가-힣]{2,10}(?:\s[가-힣]{2,10})?)\s*[\(（].*?' + re.escape(name_full.split()[0]),
            r'([가-힣]{2,10}(?:\s[가-힣]{2,10})?)\s*[-–—]\s*(?:나무위키|위키백과|나무|위키)',
            r'([가-힣]{2,10}(?:\s[가-힣]{2,10})?)\s*\|',
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if is_valid_korean_name(name):
                    korean_names.append(name)

        # 패턴 2: 나무위키 URL에서 추출
        # https://namu.wiki/w/엘런%20예거
        if 'namu.wiki/w/' in line:
            match = re.search(r'namu\.wiki/w/([가-힣%]+(?:%20[가-힣%]+)*)', line)
            if match:
                try:
                    from urllib.parse import unquote
                    name = unquote(match.group(1))
                    name = re.sub(r'\([^)]*\)$', '', name).strip()
                    if is_valid_korean_name(name):
                        korean_names.append(name)
                except:
                    pass

    # 가장 많이 나온 이름 반환
    if korean_names:
        from collections import Counter
        counter = Counter(korean_names)
        most_common = counter.most_common(1)[0][0]
        return most_common

    return None


async def search_google_for_korean_name(page, name_full):
    """구글에서 한국어 이름 검색"""
    search_query = f'"{name_full}" 이름'

    try:
        # 구글 검색
        await page.goto(
            f"https://www.google.com/search?q={search_query}&hl=ko&gl=kr",
            timeout=PAGE_TIMEOUT,
            wait_until='domcontentloaded'
        )

        await asyncio.sleep(1)

        # 페이지 텍스트 추출
        page_text = await page.evaluate("document.body.innerText")

        # 한국어 이름 추출
        korean_name = extract_korean_name_from_google(page_text, name_full)

        return korean_name

    except PlaywrightTimeout:
        log_error(f"Timeout searching for {name_full}")
        return None
    except Exception as e:
        log_error(f"Error searching for {name_full}: {e}")
        return None


async def worker(worker_id, queue, playwright, total_count, progress):
    """Worker - 구글 검색 수행"""
    global processed_count, success_count, updated_count

    browser = None
    context = None
    page = None

    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ko-KR'
        )
        page = await context.new_page()
        log(f"Worker {worker_id}: 시작")

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
            found_korean = await search_google_for_korean_name(page, name_full)

            async with lock:
                processed_count += 1
                current = processed_count

                if found_korean:
                    success_count += 1

                    if current_korean != found_korean:
                        # 업데이트 필요
                        db.execute_update(
                            "UPDATE character SET name_korean = ? WHERE id = ?",
                            (found_korean, char_id)
                        )
                        updated_count += 1
                        progress["updated"][str(char_id)] = {
                            "name_full": name_full,
                            "old": current_korean,
                            "new": found_korean
                        }
                        log(f"✓ [{current}/{total_count}] {name_full}: {current_korean or '(없음)'} → {found_korean}")
                    else:
                        # 동일
                        progress["same"].append(char_id)
                        log(f"= [{current}/{total_count}] {name_full}: {found_korean} (동일)")
                else:
                    progress["not_found"].append(char_id)
                    log(f"✗ [{current}/{total_count}] {name_full}")

                progress["processed_ids"].append(char_id)

                # 20개마다 저장
                if current % 20 == 0:
                    log(f"\n📊 진행: {current}/{total_count} | 찾음: {success_count} | 업데이트: {updated_count}\n")
                    save_progress(progress)

            # 구글 rate limit 대응
            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        log_error(f"Worker {worker_id} error: {e}")

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
    log("🔍 구글 검색으로 공식 한국어 이름 업데이트")
    log(f"   Worker: {MAX_WORKERS}개 | 딜레이: {REQUEST_DELAY}초")
    log("=" * 60)

    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행: {len(processed_ids)}개 처리됨")
        log(f"   업데이트: {len(progress.get('updated', {}))}개")

    log("\n📋 캐릭터 조회 중...")
    characters = get_characters_to_update(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 (인기도 100 이상)")

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
    start_time = datetime.now()

    async with async_playwright() as p:
        workers = [
            worker(i, queue, p, total_count, progress)
            for i in range(MAX_WORKERS)
        ]
        await asyncio.gather(*workers)

    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n{'='*60}")
    log("🎉 완료!")
    log(f"  처리: {processed_count}개")
    log(f"  찾음: {success_count}개 ({success_count/max(processed_count,1)*100:.1f}%)")
    log(f"  업데이트: {updated_count}개")
    log(f"  시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
