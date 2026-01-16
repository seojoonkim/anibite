#!/usr/bin/env python3
"""
종합 일본어→한국어 캐릭터 이름 매칭 시스템

순서:
1. Wikipedia 언어링크 (가장 빠르고 정확, 배치 처리)
2. 나무위키 애니메이션 기반 (중간 속도, 높은 커버리지)

목표: 90%+ 커버리지
"""
import sys
import os
import re
import time
import asyncio
import requests
from urllib.parse import quote, unquote
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed")
    sys.exit(1)


# Configuration
WIKI_BATCH_SIZE = 50
WIKI_MAX_WORKERS = 10
NAMU_MAX_WORKERS = 5
NAMU_REQUEST_DELAY = 0.8

USER_AGENT = "AnipassBot/1.0 (https://github.com/anipass; contact@anipass.app)"


def log(msg):
    print(msg, flush=True)


# ==================== 공통 함수 ====================

def extract_kanji(text):
    """한자만 추출"""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def is_valid_korean_name(text):
    """한글 캐릭터 이름 유효성"""
    if not text:
        return False

    # 괄호 내용 제거
    text = re.sub(r'\s*\([^)]*\)\s*$', '', text).strip()

    if len(text) > 20:
        return False

    if not re.search(r'[가-힣]', text):
        return False

    blacklist = ['목록', '등장인물', '작품', '시리즈', '분류', '캐릭터', '애니메이션',
                 '목차', '개요', '편집', '토론', '역사', '더보기', '각주']
    for word in blacklist:
        if word in text:
            return False

    return True


def get_remaining_characters(limit=None):
    """한국어 이름이 없는 캐릭터"""
    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.favourites
        FROM character c
        WHERE c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_native != ''
          AND LENGTH(c.name_native) >= 2
        ORDER BY c.favourites DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    return db.execute_query(query)


def get_anime_with_unmapped_characters(limit=None):
    """한국어 이름이 필요한 캐릭터가 있는 애니메이션"""
    query = """
        SELECT DISTINCT
            a.id,
            a.title_korean,
            a.title_romaji,
            a.popularity
        FROM anime a
        JOIN anime_character ac ON a.id = ac.anime_id
        JOIN character c ON ac.character_id = c.id
        WHERE a.title_korean IS NOT NULL
          AND c.name_korean IS NULL
          AND c.name_native IS NOT NULL
        GROUP BY a.id
        ORDER BY a.popularity DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    return db.execute_query(query)


def get_characters_for_anime(anime_id):
    """특정 애니메이션의 한국어 이름이 없는 캐릭터"""
    return db.execute_query("""
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native
        FROM character c
        JOIN anime_character ac ON c.id = ac.character_id
        WHERE ac.anime_id = ?
          AND c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_native != ''
    """, (anime_id,))


# ==================== Phase 1: Wikipedia Langlinks ====================

wiki_processed = 0
wiki_success = 0
wiki_lock = threading.Lock()


def get_korean_names_batch_wiki(jp_names):
    """Wikipedia API 배치 요청"""
    results = {}

    url = "https://ja.wikipedia.org/w/api.php"
    titles = "|".join(jp_names)

    params = {
        "action": "query",
        "prop": "langlinks",
        "titles": titles,
        "lllang": "ko",
        "format": "json",
        "lllimit": "500",
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        normalized = {n.get("to"): n.get("from")
                     for n in data.get("query", {}).get("normalized", [])}

        for page_id, page in pages.items():
            if page_id == "-1":
                continue

            title = page.get("title", "")
            langlinks = page.get("langlinks", [])

            if langlinks:
                korean_name = langlinks[0]["*"]
                original_title = normalized.get(title, title)
                results[original_title] = korean_name

    except Exception as e:
        pass

    return results


def process_wiki_batch(characters):
    """Wikipedia 배치 처리"""
    global wiki_processed, wiki_success

    jp_names = [char['name_native'] for char in characters]
    char_map = {char['name_native']: char for char in characters}

    results = get_korean_names_batch_wiki(jp_names)

    local_success = 0

    for jp_name, korean_name in results.items():
        if jp_name in char_map and is_valid_korean_name(korean_name):
            char = char_map[jp_name]
            clean_name = re.sub(r'\s*\([^)]*\)\s*$', '', korean_name).strip()

            db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (clean_name, char['id'])
            )
            local_success += 1

    with wiki_lock:
        wiki_processed += len(characters)
        wiki_success += local_success

    return local_success


def run_wikipedia_phase(characters):
    """Phase 1: Wikipedia 언어링크"""
    global wiki_processed, wiki_success
    wiki_processed = 0
    wiki_success = 0

    log("\n" + "=" * 60)
    log("📚 Phase 1: Wikipedia 언어링크")
    log("=" * 60)

    total = len(characters)
    log(f"   처리 대상: {total}개 캐릭터")

    # 배치 분할
    batches = []
    for i in range(0, len(characters), WIKI_BATCH_SIZE):
        batches.append(characters[i:i + WIKI_BATCH_SIZE])

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=WIKI_MAX_WORKERS) as executor:
        futures = [executor.submit(process_wiki_batch, batch) for batch in batches]

        for i, future in enumerate(as_completed(futures)):
            try:
                future.result()
            except Exception as e:
                pass

            # 진행상황 (25%마다)
            progress = (i + 1) / len(batches)
            if progress >= 0.25 and (i == 0 or (i + 1) % (len(batches) // 4) == 0):
                log(f"   진행: {wiki_processed}/{total} ({wiki_processed/total*100:.0f}%)")

            time.sleep(0.05)

    elapsed = time.time() - start_time
    rate = wiki_success / wiki_processed * 100 if wiki_processed > 0 else 0

    log(f"\n   ✅ 완료: {wiki_success}개 성공 ({rate:.1f}%)")
    log(f"   ⏱️  소요: {elapsed:.1f}초")

    return wiki_success


# ==================== Phase 2: 나무위키 애니메이션 기반 ====================

namu_processed = 0
namu_success = 0
namu_lock = asyncio.Lock()


def match_character_namu(char_native, char_english, page_text):
    """나무위키 페이지에서 캐릭터 매칭"""
    char_kanji = extract_kanji(char_native)

    if len(char_kanji) < 2:
        char_kanji = char_native

    lines = page_text.split('\n')

    for i, line in enumerate(lines[:200]):
        if ('/' in line or '｜' in line or '|' in line) and re.search(r'[A-Za-z]', line):
            line_kanji = extract_kanji(line)

            if char_kanji and line_kanji and char_kanji == line_kanji:
                for j in range(max(0, i-5), i):
                    prev = lines[j].strip()
                    if re.match(r'^[가-힣]+(\s[가-힣]+)?$', prev):
                        clean = prev.replace(' ', '')
                        if 2 <= len(clean) <= 10:
                            blacklist = ['목차', '개요', '등장인물', '설명', '분류', '편집']
                            if prev not in blacklist:
                                return prev

    return None


async def process_anime_namu(context, anime, total_count):
    """나무위키 애니메이션 페이지 처리"""
    global namu_processed, namu_success

    anime_id = anime['id']
    title_korean = anime['title_korean']

    chars = get_characters_for_anime(anime_id)
    if not chars:
        return 0

    page = await context.new_page()
    local_updated = 0

    try:
        urls_to_try = [
            f"https://namu.wiki/w/{quote(title_korean)}/등장인물",
            f"https://namu.wiki/w/{quote(title_korean)}",
        ]

        page_text = None

        for url in urls_to_try:
            try:
                await page.goto(url, timeout=15000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(0.5)

                text = await page.evaluate("document.body.innerText")

                if "해당 문서를 찾을 수 없습니다" not in text:
                    page_text = text
                    break

            except:
                pass

        if not page_text:
            return 0

        for char in chars:
            char_id = char['id']
            char_name = char['name_full']
            char_native = char['name_native']

            korean_name = match_character_namu(char_native, char_name, page_text)

            if korean_name:
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                local_updated += 1

            await asyncio.sleep(NAMU_REQUEST_DELAY / 3)

    finally:
        await page.close()

    async with namu_lock:
        namu_processed += 1
        namu_success += local_updated

        if local_updated > 0:
            log(f"   ✓ {title_korean}: {local_updated}개")

    return local_updated


async def namu_worker(worker_id, queue, context, total_count):
    """나무위키 워커"""
    while True:
        try:
            anime = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        try:
            await process_anime_namu(context, anime, total_count)
        except:
            pass


async def run_namuwiki_phase_async():
    """Phase 2: 나무위키 애니메이션 기반"""
    global namu_processed, namu_success
    namu_processed = 0
    namu_success = 0

    log("\n" + "=" * 60)
    log("🌿 Phase 2: 나무위키 애니메이션 기반")
    log("=" * 60)

    anime_list = get_anime_with_unmapped_characters()
    total_count = len(anime_list)

    log(f"   처리 대상: {total_count}개 애니메이션")

    if total_count == 0:
        log("   ℹ️  처리할 애니메이션 없음")
        return 0

    queue = asyncio.Queue()
    for anime in anime_list:
        await queue.put(anime)

    start_time = datetime.now()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        workers = [
            namu_worker(i, queue, context, total_count)
            for i in range(NAMU_MAX_WORKERS)
        ]

        await asyncio.gather(*workers)

        await context.close()
        await browser.close()

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n   ✅ 완료: {namu_success}개 성공")
    log(f"   ⏱️  소요: {elapsed/60:.1f}분")

    return namu_success


def run_namuwiki_phase():
    """나무위키 Phase 래퍼"""
    return asyncio.run(run_namuwiki_phase_async())


# ==================== 메인 ====================

def main():
    log("=" * 60)
    log("🚀 종합 일본어→한국어 캐릭터 이름 매칭")
    log("=" * 60)

    # 초기 상태
    initial_chars = get_remaining_characters()
    initial_count = len(initial_chars)

    log(f"\n📊 초기 상태")
    log(f"   한국어 이름 필요: {initial_count}개 캐릭터")

    if initial_count == 0:
        log("\n✅ 모든 캐릭터가 이미 한국어 이름을 가지고 있습니다!")
        return

    total_start = time.time()
    total_success = 0

    # Phase 1: Wikipedia
    chars_for_wiki = get_remaining_characters()
    wiki_success = run_wikipedia_phase(chars_for_wiki)
    total_success += wiki_success

    # Phase 2: 나무위키
    namu_success = run_namuwiki_phase()
    total_success += namu_success

    # 최종 결과
    total_elapsed = time.time() - total_start
    final_remaining = len(get_remaining_characters())
    coverage = (initial_count - final_remaining) / initial_count * 100 if initial_count > 0 else 0

    log("\n" + "=" * 60)
    log("🎉 최종 결과")
    log("=" * 60)
    log(f"   초기: {initial_count}개")
    log(f"   성공: {total_success}개")
    log(f"   남은 캐릭터: {final_remaining}개")
    log(f"   커버리지: {coverage:.1f}%")
    log(f"   총 소요 시간: {total_elapsed/60:.1f}분")
    log("=" * 60)


if __name__ == "__main__":
    main()
