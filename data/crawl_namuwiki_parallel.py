"""
Parallel crawl character Korean names from Namuwiki
5개 브라우저로 병렬 크롤링, 10개마다 결과 출력
"""
import sys
import os
import re
import asyncio
import json
from urllib.parse import quote
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# Force unbuffered output
import functools
print = functools.partial(print, flush=True)

# Configuration
NUM_WORKERS = 5
MAX_LINKS_PER_ANIME = 50
REQUEST_DELAY = 0.3
REPORT_INTERVAL = 10

# Thread-safe counters
verified_count = 0
processed_count = 0


def get_characters_without_korean_names():
    """Get characters that need Korean names"""
    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.favourites,
            a.title_korean,
            a.title_romaji,
            ac.role
        FROM character c
        JOIN anime_character ac ON c.id = ac.character_id
        JOIN anime a ON ac.anime_id = a.id
        WHERE c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_native != ''
          AND a.title_korean IS NOT NULL
        ORDER BY c.favourites DESC
    """
    return db.execute_query(query)


def normalize_name(name):
    """Normalize name for comparison"""
    if not name:
        return ''
    name = re.sub(r'\s+', '', name.lower())
    name = re.sub(r'[・\-_\.\[\]0-9]', '', name)
    return name


def is_pure_korean(name):
    """Check if name contains only Korean characters"""
    if not name:
        return False
    for char in name:
        if char in ' ・-=':
            continue
        if '\uAC00' <= char <= '\uD7A3':
            continue
        if '\u1100' <= char <= '\u11FF':
            continue
        return False
    return True


def verify_match(db_native, db_english, wiki_japanese, wiki_english):
    """Verify if the wiki data matches the database character"""
    db_native_norm = normalize_name(db_native)
    wiki_jp_norm = normalize_name(wiki_japanese)

    if db_native_norm == wiki_jp_norm:
        return True
    if db_native_norm in wiki_jp_norm or wiki_jp_norm in db_native_norm:
        return True

    if db_english and wiki_english:
        db_en_norm = normalize_name(db_english)
        wiki_en_norm = normalize_name(wiki_english)
        if db_en_norm == wiki_en_norm:
            return True
        db_en_parts = set(db_english.lower().split())
        wiki_en_parts = set(wiki_english.lower().split()) if wiki_english else set()
        if db_en_parts and wiki_en_parts:
            if len(db_en_parts.intersection(wiki_en_parts)) >= 2:
                return True

    return False


def extract_japanese_name(text):
    """Extract Japanese name from page text"""
    lines = text.split('\n')
    for line in lines:
        if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+.*[|｜].*[A-Za-z]', line):
            parts = re.split(r'[|｜]', line)
            if parts:
                jp_part = parts[0].strip()
                kanji_only = re.sub(r'[\u3040-\u309f]', '', jp_part)
                kanji_only = re.sub(r'\s+', '', kanji_only)
                en_part = parts[1].strip() if len(parts) > 1 else None
                if kanji_only and len(kanji_only) >= 2:
                    return {'japanese': kanji_only, 'english': en_part}
    return None


async def crawl_anime_page(page, title_korean):
    """Crawl anime character list page"""
    urls = [
        f"https://namu.wiki/w/{quote(title_korean)}/등장인물",
        f"https://namu.wiki/w/{quote(title_korean)}",
    ]

    for url in urls:
        try:
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.2)

            text = await page.evaluate("document.body.innerText")
            if "해당 문서를 찾을 수 없습니다" in text:
                continue

            links = await page.evaluate("""
                () => {
                    const links = [];
                    const seen = new Set();
                    const blacklist = ['소설','만화','영역','애니','게임','시리즈','목차','개요',
                        '설정','줄거리','등장인물','비판','논란','미디어','기타','사변',
                        '회전','고전','전개','인물','관계','행적','능력','평가','여담',
                        '각주','외부','링크','분류','편집','역사','성우','작가','감독',
                        '제작','방영','출판','연재'];

                    document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                        const href = a.getAttribute('href');
                        const text = a.innerText.trim();
                        if (seen.has(text)) return;
                        if (!/^[가-힣\\s]{2,15}$/.test(text)) return;
                        if (text.includes('/')) return;
                        for (const w of blacklist) if (text.includes(w)) return;
                        if (href.includes('/분류:') || href.includes('#')) return;
                        if (text.includes(' ') && text.length >= 4) {
                            seen.add(text);
                            links.push({href, text});
                        }
                    });
                    return links;
                }
            """)
            return links
        except:
            continue
    return []


async def crawl_character_page(page, korean_name):
    """Crawl individual character page"""
    try:
        await page.goto(f"https://namu.wiki/w/{quote(korean_name)}", timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.15)
        text = await page.evaluate("document.body.innerText")
        if "해당 문서를 찾을 수 없습니다" in text:
            return None
        return extract_japanese_name(text)
    except:
        return None


async def worker(worker_id, char_queue, all_mappings, mappings_lock,
                processed_anime, anime_lock, results, results_lock, total_chars):
    """Worker that processes characters"""
    global verified_count, processed_count

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        while True:
            try:
                char = char_queue.popleft()
            except IndexError:
                break

            char_id = char['id']
            name_full = char['name_full']
            name_native = char['name_native']
            title_korean = char['title_korean']

            processed_count += 1

            # Check cached mapping
            async with mappings_lock:
                if name_native in all_mappings:
                    mapping = all_mappings[name_native]
                    if verify_match(name_native, name_full, mapping['japanese'], mapping.get('english')):
                        if is_pure_korean(mapping['korean']):
                            db.execute_update(
                                "UPDATE character SET name_korean = ? WHERE id = ?",
                                (mapping['korean'], char_id)
                            )
                            verified_count += 1
                            async with results_lock:
                                results.append({'english': name_full, 'korean': mapping['korean']})
                                if verified_count % REPORT_INTERVAL == 0:
                                    print(f"\n{'='*70}")
                                    print(f"  [진행 보고] {verified_count}개 완료 (처리: {processed_count}/{len(char_queue)+processed_count})")
                                    print(f"{'='*70}")
                                    for i, r in enumerate(results[-REPORT_INTERVAL:], 1):
                                        print(f"    {i}. {r['english']}: {r['korean']}")
                                    print(f"{'='*70}\n")
                            continue

            # Check if anime already processed
            async with anime_lock:
                if title_korean in processed_anime:
                    continue
                processed_anime.add(title_korean)

            # Crawl anime page
            char_links = await crawl_anime_page(page, title_korean)

            if char_links:
                for link in char_links[:MAX_LINKS_PER_ANIME]:
                    kr_name = link['text']

                    async with mappings_lock:
                        if any(m['korean'] == kr_name for m in all_mappings.values()):
                            continue

                    wiki_data = await crawl_character_page(page, kr_name)

                    if wiki_data and wiki_data.get('japanese'):
                        jp_name = wiki_data['japanese']
                        async with mappings_lock:
                            all_mappings[jp_name] = {
                                'korean': kr_name,
                                'japanese': jp_name,
                                'english': wiki_data.get('english')
                            }

                    await asyncio.sleep(REQUEST_DELAY)

            # Try match again after crawling
            async with mappings_lock:
                if name_native in all_mappings:
                    mapping = all_mappings[name_native]
                    if verify_match(name_native, name_full, mapping['japanese'], mapping.get('english')):
                        if is_pure_korean(mapping['korean']):
                            db.execute_update(
                                "UPDATE character SET name_korean = ? WHERE id = ?",
                                (mapping['korean'], char_id)
                            )
                            verified_count += 1
                            async with results_lock:
                                results.append({'english': name_full, 'korean': mapping['korean']})
                                if verified_count % REPORT_INTERVAL == 0:
                                    print(f"\n{'='*70}")
                                    print(f"  [진행 보고] {verified_count}개 완료 (처리: {processed_count}/{len(char_queue)+processed_count})")
                                    print(f"{'='*70}")
                                    for i, r in enumerate(results[-REPORT_INTERVAL:], 1):
                                        print(f"    {i}. {r['english']}: {r['korean']}")
                                    print(f"{'='*70}\n")

        await browser.close()
        print(f"  [Worker {worker_id}] 종료")


async def main():
    """Main function"""
    total_chars = db.execute_query("SELECT COUNT(*) as c FROM character", fetch_one=True)['c']
    with_korean = db.execute_query(
        "SELECT COUNT(*) as c FROM character WHERE name_korean IS NOT NULL", fetch_one=True
    )['c']

    print("=" * 70)
    print(f"  나무위키 캐릭터 한국어 이름 크롤러 (병렬 {NUM_WORKERS}개)")
    print(f"  시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n  [DB 현황]")
    print(f"  - 전체 캐릭터: {total_chars:,}개")
    print(f"  - 한국어 이름 있음: {with_korean:,}개 ({with_korean/total_chars*100:.1f}%)")
    print(f"  - 한국어 이름 필요: {total_chars - with_korean:,}개")
    print("=" * 70)

    characters = get_characters_without_korean_names()
    print(f"\n처리 대상: {len(characters)}개 캐릭터\n")

    if not characters:
        print("한국어 이름이 필요한 캐릭터가 없습니다!")
        return

    # Shared state
    char_queue = deque(characters)
    all_mappings = {}
    mappings_lock = asyncio.Lock()
    processed_anime = set()
    anime_lock = asyncio.Lock()
    results = []
    results_lock = asyncio.Lock()

    # Start workers
    workers = [
        asyncio.create_task(
            worker(i, char_queue, all_mappings, mappings_lock,
                   processed_anime, anime_lock, results, results_lock, total_chars)
        )
        for i in range(NUM_WORKERS)
    ]

    await asyncio.gather(*workers)

    # Final stats
    new_with_korean = db.execute_query(
        "SELECT COUNT(*) as c FROM character WHERE name_korean IS NOT NULL", fetch_one=True
    )['c']

    print(f"\n{'='*70}")
    print("  크롤링 완료!")
    print(f"{'='*70}")
    print(f"  - 이번에 추가됨: {new_with_korean - with_korean:,}개")
    print(f"  - 한국어 이름 있음: {new_with_korean:,}개 ({new_with_korean/total_chars*100:.1f}%)")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
