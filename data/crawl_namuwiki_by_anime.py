#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 - 애니메이션 기반
애니메이션 등장인물 페이지에서 캐릭터 이름 매핑 추출

5개 병렬 Worker, 10개마다 진행상황
"""
import sys
import os
import re
import asyncio
from urllib.parse import quote, unquote
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed")
    sys.exit(1)


# Configuration
MAX_WORKERS = 5
MAX_ANIME = 30  # None = 전체, 테스트용
REQUEST_DELAY = 0.8


# Global counters
processed_anime = 0
updated_characters = 0
lock = asyncio.Lock()


def log(msg):
    print(msg, flush=True)


def extract_kanji(text):
    """한자만 추출"""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def get_anime_to_process(limit=None):
    """한국어 제목이 있고 캐릭터 한국어 이름이 필요한 애니메이션"""
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
    """특정 애니메이션의 한국어 이름이 없는 캐릭터들"""
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


def match_character(char_native, char_english, page_text):
    """
    페이지 텍스트에서 캐릭터 매칭 후 한글 이름 반환

    나무위키 캐릭터 인포박스 형식:
    한글이름
    日本語名｜English Name
    """
    char_kanji = extract_kanji(char_native)

    if len(char_kanji) < 2:
        char_kanji = char_native

    lines = page_text.split('\n')

    for i, line in enumerate(lines[:200]):
        # 일본어|영어 또는 일본어/영어 패턴
        if ('/' in line or '｜' in line or '|' in line) and re.search(r'[A-Za-z]', line):
            line_kanji = extract_kanji(line)

            # 한자 정확 일치
            if char_kanji and line_kanji and char_kanji == line_kanji:
                # 이전 줄에서 한글 이름 찾기
                for j in range(max(0, i-5), i):
                    prev = lines[j].strip()
                    # 순수 한글 이름 (2-10자)
                    if re.match(r'^[가-힣]+(\s[가-힣]+)?$', prev):
                        clean = prev.replace(' ', '')
                        if 2 <= len(clean) <= 10:
                            # 비이름 필터
                            blacklist = ['목차', '개요', '등장인물', '설명', '분류', '편집']
                            if prev not in blacklist:
                                return prev

    return None


async def process_anime(context, anime, total_count):
    """애니메이션의 등장인물 페이지에서 캐릭터 이름 추출"""
    global processed_anime, updated_characters

    anime_id = anime['id']
    title_korean = anime['title_korean']

    chars = get_characters_for_anime(anime_id)
    if not chars:
        return

    page = await context.new_page()
    local_updated = 0

    try:
        # 등장인물 페이지 시도
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
            return

        # 각 캐릭터에 대해 개별 페이지도 확인
        for char in chars:
            char_id = char['id']
            char_name = char['name_full']
            char_native = char['name_native']

            # 먼저 등장인물 페이지에서 매칭 시도
            korean_name = match_character(char_native, char_name, page_text)

            # 못 찾았으면 개별 캐릭터 페이지 시도 (한글 추측)
            if not korean_name:
                # 일본어 이름의 한글 읽음 추측은 어려우므로 스킵
                pass

            if korean_name:
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                local_updated += 1

            await asyncio.sleep(REQUEST_DELAY / 3)

    finally:
        await page.close()

    async with lock:
        processed_anime += 1
        updated_characters += local_updated
        current = processed_anime

        if local_updated > 0:
            log(f"✓ [{current}/{total_count}] {title_korean}: {local_updated}개 업데이트")
        else:
            log(f"✗ [{current}/{total_count}] {title_korean}")

        if current % 10 == 0:
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
            log(f"   총 업데이트: {updated_characters}개 캐릭터")
            log(f"{'='*60}\n")


async def worker(worker_id, queue, context, total_count):
    """Worker"""
    while True:
        try:
            anime = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        try:
            await process_anime(context, anime, total_count)
        except Exception as e:
            pass


async def main():
    global processed_anime, updated_characters

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 (애니메이션 기반)")
    log(f"   {MAX_WORKERS}개 병렬 Worker")
    log("=" * 60)

    log("\n📋 처리할 애니메이션 조회 중...")
    anime_list = get_anime_to_process(limit=MAX_ANIME)
    total_count = len(anime_list)

    log(f"   총 {total_count}개 애니메이션 발견")

    if total_count == 0:
        log("✅ 처리할 애니메이션이 없습니다!")
        return

    processed_anime = 0
    updated_characters = 0

    queue = asyncio.Queue()
    for anime in anime_list:
        await queue.put(anime)

    log(f"\n🔄 크롤링 시작 ({MAX_WORKERS}개 Worker)...")
    start_time = datetime.now()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        workers = [
            worker(i, queue, context, total_count)
            for i in range(MAX_WORKERS)
        ]

        await asyncio.gather(*workers)

        await context.close()
        await browser.close()

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n\n{'='*60}")
    log("🎉 크롤링 완료!")
    log(f"{'='*60}")
    log(f"  처리 애니메이션: {processed_anime}개")
    log(f"  업데이트 캐릭터: {updated_characters}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
