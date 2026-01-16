"""
Crawl character Korean names from Namuwiki with verification
검증을 포함한 나무위키 캐릭터 한국어 이름 크롤링
"""
import sys
import os
import re
import time
import asyncio
import json
from urllib.parse import quote, unquote
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# Force unbuffered output
import functools
print = functools.partial(print, flush=True)

# Configuration
MAX_CHARACTERS = 1000  # Target number of characters to process
MAX_LINKS_PER_ANIME = 50  # Max character links to crawl per anime
REQUEST_DELAY = 1.0  # seconds between requests
SAVE_INTERVAL = 50  # Save progress every N characters


def get_characters_without_korean_names(limit=None):
    """Get characters that need Korean names, grouped by anime"""
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
    if limit:
        query += f" LIMIT {limit}"

    return db.execute_query(query)


def extract_japanese_name(text):
    """Extract Japanese name from page text"""
    lines = text.split('\n')

    for line in lines:
        # Look for pattern: 日本語名｜English Name
        if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+.*[|｜].*[A-Za-z]', line):
            parts = re.split(r'[|｜]', line)
            if parts:
                jp_part = parts[0].strip()
                # Remove furigana (hiragana) - keep only kanji
                kanji_only = re.sub(r'[\u3040-\u309f]', '', jp_part)
                kanji_only = re.sub(r'\s+', '', kanji_only)

                # Also get English name
                en_part = parts[1].strip() if len(parts) > 1 else None

                if kanji_only and len(kanji_only) >= 2:
                    return {'japanese': kanji_only, 'english': en_part}

    return None


def normalize_name(name):
    """Normalize name for comparison"""
    if not name:
        return ''
    # Remove spaces, convert to lowercase
    name = re.sub(r'\s+', '', name.lower())
    # Remove common punctuation
    name = re.sub(r'[・\-_\.]', '', name)
    return name


def verify_match(db_native, db_english, wiki_japanese, wiki_english):
    """Verify if the wiki data matches the database character"""
    # Normalize all names
    db_native_norm = normalize_name(db_native)
    wiki_jp_norm = normalize_name(wiki_japanese)

    # Primary check: Japanese names should match
    if db_native_norm == wiki_jp_norm:
        return True, "exact_japanese_match"

    # Check if one contains the other (for names with variations)
    if db_native_norm in wiki_jp_norm or wiki_jp_norm in db_native_norm:
        return True, "partial_japanese_match"

    # If Japanese doesn't match but English does, still accept with caution
    if db_english and wiki_english:
        db_en_norm = normalize_name(db_english)
        wiki_en_norm = normalize_name(wiki_english)

        if db_en_norm == wiki_en_norm:
            return True, "english_match"

        # Check partial English match
        db_en_parts = set(db_english.lower().split())
        wiki_en_parts = set(wiki_english.lower().split()) if wiki_english else set()

        if db_en_parts and wiki_en_parts:
            overlap = db_en_parts.intersection(wiki_en_parts)
            if len(overlap) >= 2:  # At least 2 name parts match
                return True, "partial_english_match"

    return False, "no_match"


async def crawl_anime_characters_page(page, anime_title_korean):
    """Crawl anime character list page and extract character links"""
    urls_to_try = [
        f"https://namu.wiki/w/{quote(anime_title_korean)}/등장인물",
        f"https://namu.wiki/w/{quote(anime_title_korean)}",
    ]

    for url in urls_to_try:
        try:
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.3)

            text = await page.evaluate("document.body.innerText")

            if "해당 문서를 찾을 수 없습니다" in text:
                continue

            # Extract character links
            character_links = await page.evaluate("""
                () => {
                    const links = [];
                    const seen = new Set();

                    const blacklist = [
                        '소설', '만화', '영역', '애니', '게임', '시리즈', '목차', '개요',
                        '설정', '줄거리', '등장인물', '비판', '논란', '미디어', '기타',
                        '사변', '회전', '고전', '전개', '인물', '관계', '행적', '능력',
                        '평가', '여담', '각주', '외부', '링크', '분류', '편집', '역사',
                        '성우', '작가', '감독', '제작', '방영', '출판', '연재'
                    ];

                    document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                        const href = a.getAttribute('href');
                        const text = a.innerText.trim();

                        if (seen.has(text)) return;
                        if (!/^[가-힣\\s]{2,15}$/.test(text)) return;
                        if (text.includes('/')) return;

                        for (const word of blacklist) {
                            if (text.includes(word)) return;
                        }

                        if (href.includes('/분류:') || href.includes('#')) return;

                        if (text.includes(' ') && text.length >= 4) {
                            seen.add(text);
                            links.push({href: href, text: text});
                        }
                    });
                    return links;
                }
            """)

            return character_links

        except Exception as e:
            print(f"    Error crawling anime page: {e}")
            continue

    return []


async def crawl_character_page(page, korean_name):
    """Crawl individual character page and extract Japanese/English names"""
    url = f"https://namu.wiki/w/{quote(korean_name)}"

    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.2)

        text = await page.evaluate("document.body.innerText")

        if "해당 문서를 찾을 수 없습니다" in text:
            return None

        return extract_japanese_name(text)

    except Exception as e:
        return None


async def main():
    """Main crawling function with verification"""
    from playwright.async_api import async_playwright

    print("=" * 80)
    print("Namuwiki Character Korean Names Crawler (Verified)")
    print("나무위키 캐릭터 한국어 이름 크롤러 (검증 포함)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Get characters to process
    characters = get_characters_without_korean_names(limit=MAX_CHARACTERS * 3)  # Get more to account for failures
    print(f"\nFound {len(characters)} characters to process")

    if not characters:
        print("No characters need Korean names!")
        return

    # Results tracking
    results = {
        'verified': [],      # Successfully verified and updated
        'unverified': [],    # Found but couldn't verify
        'not_found': [],     # Couldn't find on wiki
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        processed_anime = set()
        all_mappings = {}  # japanese_name -> {korean_name, english_name}
        verified_count = 0
        processed_count = 0

        for i, char in enumerate(characters):
            if verified_count >= MAX_CHARACTERS:
                print(f"\nReached target of {MAX_CHARACTERS} verified characters!")
                break

            char_id = char['id']
            name_full = char['name_full']
            name_native = char['name_native']
            title_korean = char['title_korean']
            favourites = char['favourites']

            processed_count += 1
            print(f"\n[{processed_count}] {name_full} ({name_native}) - {favourites:,} favs")
            print(f"  Anime: {title_korean}")

            # Check if we already have a verified mapping
            if name_native in all_mappings:
                mapping = all_mappings[name_native]
                is_valid, match_type = verify_match(
                    name_native, name_full,
                    mapping['japanese'], mapping.get('english')
                )

                if is_valid:
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (mapping['korean'], char_id)
                    )
                    print(f"  ✓ Cached & Verified: {mapping['korean']} ({match_type})")
                    results['verified'].append({
                        'id': char_id, 'english': name_full, 'native': name_native,
                        'korean': mapping['korean'], 'match_type': match_type
                    })
                    verified_count += 1
                    continue

            # Crawl anime character page if not already done
            if title_korean not in processed_anime:
                print(f"  Crawling: {title_korean}/등장인물")
                character_links = await crawl_anime_characters_page(page, title_korean)
                processed_anime.add(title_korean)

                if character_links:
                    print(f"  Found {len(character_links)} character links")

                    # Visit each character page
                    for link in character_links[:MAX_LINKS_PER_ANIME]:
                        kr_name = link['text']

                        # Skip if already mapped
                        if any(m['korean'] == kr_name for m in all_mappings.values()):
                            continue

                        wiki_data = await crawl_character_page(page, kr_name)

                        if wiki_data and wiki_data.get('japanese'):
                            jp_name = wiki_data['japanese']
                            all_mappings[jp_name] = {
                                'korean': kr_name,
                                'japanese': jp_name,
                                'english': wiki_data.get('english')
                            }
                            print(f"    {kr_name} -> {jp_name}")

                        await asyncio.sleep(REQUEST_DELAY)

                await asyncio.sleep(REQUEST_DELAY)

            # Try to find and verify match
            if name_native in all_mappings:
                mapping = all_mappings[name_native]
                is_valid, match_type = verify_match(
                    name_native, name_full,
                    mapping['japanese'], mapping.get('english')
                )

                if is_valid:
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (mapping['korean'], char_id)
                    )
                    print(f"  ✓ Verified: {mapping['korean']} ({match_type})")
                    results['verified'].append({
                        'id': char_id, 'english': name_full, 'native': name_native,
                        'korean': mapping['korean'], 'match_type': match_type
                    })
                    verified_count += 1
                else:
                    print(f"  ⚠ Found but not verified: {mapping['korean']}")
                    results['unverified'].append({
                        'id': char_id, 'english': name_full, 'native': name_native,
                        'wiki_korean': mapping['korean'], 'wiki_japanese': mapping['japanese']
                    })
            else:
                print(f"  ✗ Not found")
                results['not_found'].append({
                    'id': char_id, 'english': name_full, 'native': name_native
                })

            # Save progress periodically
            if processed_count % SAVE_INTERVAL == 0:
                print(f"\n--- Progress: {verified_count}/{MAX_CHARACTERS} verified ---")

        await browser.close()

    # Final statistics
    print(f"\n{'='*80}")
    print("Crawling Complete!")
    print(f"{'='*80}")
    print(f"Total processed: {processed_count}")
    print(f"Verified & Updated: {len(results['verified'])}")
    print(f"Found but unverified: {len(results['unverified'])}")
    print(f"Not found: {len(results['not_found'])}")

    # Save results to file
    results_file = f"/tmp/namuwiki_crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {results_file}")

    # Get updated stats
    total = db.execute_query("SELECT COUNT(*) as c FROM character", fetch_one=True)['c']
    with_korean = db.execute_query(
        "SELECT COUNT(*) as c FROM character WHERE name_korean IS NOT NULL",
        fetch_one=True
    )['c']

    print(f"\nDatabase Statistics:")
    print(f"Total characters: {total:,}")
    print(f"With Korean names: {with_korean:,} ({with_korean/total*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
