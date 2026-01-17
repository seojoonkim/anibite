#!/usr/bin/env python3
"""
구글 검색 기반 캐릭터 한국어 이름 크롤러
가장 빠르고 간단한 방식

검색 쿼리: "캐릭터 영어이름" + "이름" 또는 site:namu.wiki
첫 번째 결과에서 한국어 이름 추출
"""
import sys
import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, quote

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
MAX_CONCURRENT = 5  # 구글은 rate limit이 빡세서 적게
MAX_CHARACTERS = None
REQUEST_TIMEOUT = 15

PROGRESS_FILE = Path(__file__).parent / "crawl_progress_google.json"
ERROR_LOG_FILE = Path(__file__).parent / "crawl_errors_google.log"

# Global
processed_count = 0
success_count = 0
error_count = 0
lock = asyncio.Lock()
semaphore = None


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
    return {"processed_ids": [], "success": {}, "failed": []}


def save_progress(progress):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except:
        pass


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
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
                 '나무위키', '검색', '결과']
    if text in blacklist or any(b in text for b in blacklist):
        return False
    return True


def extract_korean_from_url(url):
    """URL에서 한국어 이름 추출 (나무위키 URL 패턴)"""
    # namu.wiki/w/엘런 예거 형태
    if 'namu.wiki/w/' in url:
        try:
            path = url.split('/w/')[-1]
            decoded = unquote(path)
            # 괄호 제거 (동명이인 구분용)
            name = re.sub(r'\([^)]*\)$', '', decoded).strip()
            if is_valid_korean_name(name):
                return name
        except:
            pass
    return None


def extract_korean_from_text(text):
    """텍스트에서 한국어 이름 추출"""
    # "XXX - 나무위키" 패턴
    match = re.search(r'^([가-힣]+(?:\s[가-힣]+)?)\s*[-–—]\s*나무위키', text)
    if match:
        name = match.group(1).strip()
        if is_valid_korean_name(name):
            return name

    # "XXX(한글) - " 패턴
    match = re.search(r'([가-힣]{2,10})\s*\(', text)
    if match:
        name = match.group(1).strip()
        if is_valid_korean_name(name):
            return name

    return None


async def search_google(client, query):
    """구글 검색 수행"""
    url = f"https://www.google.com/search?q={quote(query)}&hl=ko&gl=kr"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        async with semaphore:
            response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                log("⚠ 구글 Rate limit 감지, 30초 대기...")
                await asyncio.sleep(30)
    except Exception as e:
        log_error(f"Search error: {e}")

    return None


def parse_google_results(html, name_native, name_full):
    """구글 검색 결과 파싱"""
    soup = BeautifulSoup(html, 'html.parser')

    # 검색 결과에서 나무위키 링크 찾기
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')

        # 나무위키 URL 찾기
        if 'namu.wiki/w/' in href:
            korean_name = extract_korean_from_url(href)
            if korean_name:
                return korean_name

        # 제목에서 한국어 이름 추출
        title = a.get_text()
        if '나무위키' in title:
            korean_name = extract_korean_from_text(title)
            if korean_name:
                return korean_name

    # 검색 결과 스니펫에서 찾기
    for div in soup.find_all(['div', 'span']):
        text = div.get_text()

        # "XXX(한국어발음)" 패턴
        # 예: "エレン・イェーガー(엘런 예거)"
        pattern = rf'{re.escape(name_native[:3])}.*?\(([가-힣]{{2,10}})\)'
        match = re.search(pattern, text)
        if match:
            name = match.group(1)
            if is_valid_korean_name(name):
                return name

    return None


async def find_korean_name_google(client, name_native, name_full):
    """구글 검색으로 한국어 이름 찾기"""

    # 전략 1: 일본어 이름 + site:namu.wiki
    query = f'"{name_native}" site:namu.wiki'
    html = await search_google(client, query)
    if html:
        result = parse_google_results(html, name_native, name_full)
        if result:
            return result

    await asyncio.sleep(1)  # 구글 rate limit 대응

    # 전략 2: 영어 이름 + "이름" + 애니메이션
    query = f'{name_full} 이름 캐릭터'
    html = await search_google(client, query)
    if html:
        result = parse_google_results(html, name_native, name_full)
        if result:
            return result

    await asyncio.sleep(1)

    # 전략 3: 영어 이름 + site:namu.wiki
    query = f'"{name_full}" site:namu.wiki'
    html = await search_google(client, query)
    if html:
        result = parse_google_results(html, name_native, name_full)
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
        korean_name = await find_korean_name_google(client, name_native, name_full)

        if korean_name:
            db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (korean_name, char_id)
            )

    except Exception as e:
        error_occurred = True
        log_error(f"Error on {name_full}: {e}")

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

        if current % 20 == 0:
            rate = success_count / current * 100 if current > 0 else 0
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
            log(f"   성공: {success_count}개 ({rate:.1f}%)")
            log(f"   에러: {error_count}개")
            log(f"{'='*60}\n")
            save_progress(progress)


async def main():
    global processed_count, success_count, error_count, semaphore

    log("=" * 60)
    log("🔍 구글 검색 기반 캐릭터 한국어 이름 크롤러")
    log(f"   동시 요청: {MAX_CONCURRENT}개")
    log("=" * 60)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행 상황: {len(processed_ids)}개 처리됨")
        log(f"   성공: {len(progress.get('success', {}))}개")

    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0
    error_count = 0

    log(f"\n🔄 크롤링 시작...")
    start_time = datetime.now()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 순차 처리 (구글 rate limit 때문에)
        for char in characters:
            await process_character(client, char, total_count, progress)
            await asyncio.sleep(2)  # 구글 rate limit 대응

    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n\n{'='*60}")
    log("🎉 크롤링 완료!")
    log(f"{'='*60}")
    log(f"  총 처리: {processed_count}개")
    if processed_count > 0:
        log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
        log(f"  에러: {error_count}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"  속도: {processed_count / elapsed * 60:.1f}개/분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
