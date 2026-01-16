#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v2 - 애니메이션 기반
1. 애니메이션 등장인물 페이지에서 캐릭터 링크 추출
2. 각 캐릭터 페이지 방문하여 일본어→한글 매핑 생성
3. DB 캐릭터와 매칭

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
MAX_ANIME = 20  # None = 전체, 테스트용
REQUEST_DELAY = 0.5


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


def is_valid_korean_name(text):
    """한글 캐릭터 이름 유효성"""
    if not text:
        return False
    text = text.strip()
    if not re.match(r'^[가-힣]+(\s[가-힣]+)?$', text):
        return False
    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 10:
        return False
    blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '편집', '토론', '역사', '최근', '수정', '작품', '시리즈']
    if text in blacklist:
        return False
    return True


def is_character_document(page_text):
    """캐릭터 문서인지 확인"""
    header = page_text[:3000]

    # 분류에서 실존 인물 제외
    for line in header.split('\n')[:15]:
        if '분류' in line:
            if any(cat in line for cat in ['남배우', '여배우', '가수', '아이돌', '출생', '데뷔']):
                return False
            break

    # 성우 정보 필수
    return '성우' in header


def extract_japanese_name(page_text):
    """페이지에서 일본어 이름 추출 (한자 형태)"""
    lines = page_text.split('\n')[:80]

    for line in lines:
        # 일본어|영어 또는 일본어/영어 패턴
        if ('/' in line or '｜' in line or '|' in line) and re.search(r'[A-Za-z]', line):
            kanji = extract_kanji(line)
            if len(kanji) >= 2:
                return kanji

    return None


async def extract_character_links(page, title_korean):
    """등장인물 페이지에서 캐릭터 링크 추출"""
    urls_to_try = [
        f"https://namu.wiki/w/{quote(title_korean)}/등장인물",
        f"https://namu.wiki/w/{quote(title_korean)}",
    ]

    char_links = []

    for url in urls_to_try:
        try:
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.5)

            text = await page.evaluate("document.body.innerText")

            if "해당 문서를 찾을 수 없습니다" in text:
                continue

            # 캐릭터 링크 추출
            links = await page.evaluate("""
                () => {
                    const items = [];
                    const seen = new Set();

                    document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                        const href = a.getAttribute('href');
                        const text = a.innerText.trim();

                        if (href.includes('#') || href.includes(':')) return;
                        if (seen.has(href)) return;

                        // 한글 이름 패턴 (2-10자, 공백 포함)
                        if (/^[가-힣]+(?:\\s[가-힣]+)?$/.test(text)) {
                            const clean = text.replace(/\\s/g, '');
                            if (clean.length >= 2 && clean.length <= 10) {
                                seen.add(href);
                                items.push({href: href, text: text});
                            }
                        }
                    });

                    return items.slice(0, 100);
                }
            """)

            # 유효한 캐릭터 이름만 필터링
            for link in links:
                name = link['text']
                if is_valid_korean_name(name):
                    char_links.append(link)

            if char_links:
                break

        except:
            pass

    return char_links


async def process_anime(context, anime, total_count):
    """애니메이션 처리"""
    global processed_anime, updated_characters

    anime_id = anime['id']
    title_korean = anime['title_korean']

    # DB에서 이 애니메이션의 캐릭터 (일본어 이름 있는 것만)
    db_chars = get_characters_for_anime(anime_id)
    if not db_chars:
        return

    # 한자 → 캐릭터 ID 매핑
    kanji_to_char = {}
    for char in db_chars:
        kanji = extract_kanji(char['name_native'])
        if len(kanji) >= 2:
            kanji_to_char[kanji] = (char['id'], char['name_full'])

    if not kanji_to_char:
        return

    page = await context.new_page()
    local_updated = 0

    try:
        # 등장인물 페이지에서 캐릭터 링크 추출
        char_links = await extract_character_links(page, title_korean)

        if not char_links:
            return

        # 각 캐릭터 페이지 방문
        for link in char_links[:50]:  # 최대 50개
            korean_name = link['text']
            href = link['href']

            try:
                doc_url = f"https://namu.wiki{href}"
                await page.goto(doc_url, timeout=10000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(0.3)

                page_text = await page.evaluate("document.body.innerText")

                if "해당 문서를 찾을 수 없습니다" in page_text:
                    continue

                # 캐릭터 문서인지 확인
                if not is_character_document(page_text):
                    continue

                # 일본어 이름 (한자) 추출
                jp_kanji = extract_japanese_name(page_text)

                if jp_kanji and jp_kanji in kanji_to_char:
                    char_id, char_name = kanji_to_char[jp_kanji]

                    # DB 업데이트
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (korean_name, char_id)
                    )

                    # 매핑에서 제거 (중복 방지)
                    del kanji_to_char[jp_kanji]
                    local_updated += 1

            except:
                pass

            await asyncio.sleep(REQUEST_DELAY)

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
        except:
            pass


async def main():
    global processed_anime, updated_characters

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v2 (애니메이션 기반)")
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
