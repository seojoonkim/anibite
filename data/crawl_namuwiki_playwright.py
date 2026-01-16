"""
Crawl character Korean names from Namuwiki using Playwright
Playwright를 사용해 나무위키에서 캐릭터 한국어 이름 크롤링
"""
import sys
import os
import re
import time
import asyncio
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# Configuration
MAX_CHARACTERS = 50  # Set to None for all
REQUEST_DELAY = 1.5  # seconds between requests


def get_anime_with_korean_titles():
    """Get anime that have Korean titles"""
    query = """
        SELECT DISTINCT a.id, a.title_korean, a.title_romaji
        FROM anime a
        JOIN anime_character ac ON a.id = ac.anime_id
        JOIN character c ON ac.character_id = c.id
        WHERE a.title_korean IS NOT NULL
          AND c.name_korean IS NULL
          AND c.name_native IS NOT NULL
        ORDER BY a.popularity DESC
    """
    return db.execute_query(query)


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
          AND a.title_korean IS NOT NULL
        ORDER BY c.favourites DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    return db.execute_query(query)


async def crawl_character_page(page, korean_name):
    """Crawl a single character page and extract Japanese name mapping"""
    url = f"https://namu.wiki/w/{quote(korean_name)}"

    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)

        # Get page content
        content = await page.content()
        text = await page.evaluate("document.body.innerText")

        # Look for Japanese name pattern
        # Pattern: 한글이름 \n 日本語名｜English Name
        # Or in the info box

        # Extract Japanese name from content
        japanese_name = extract_japanese_name(text, korean_name)

        return {
            'korean_name': korean_name,
            'japanese_name': japanese_name,
            'url': url,
            'found': japanese_name is not None
        }

    except Exception as e:
        print(f"  Error crawling {korean_name}: {e}")
        return None


def extract_japanese_name(text, korean_name):
    """Extract Japanese name from page text"""
    # Look for patterns like:
    # 고죠 사토루
    # 五ご条じょう 悟さとる｜Satoru Gojo
    # The furigana (small hiragana) is mixed in

    lines = text.split('\n')

    for i, line in enumerate(lines):
        # Look for Japanese characters followed by | or ｜ and English
        if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+.*[|｜].*[A-Za-z]', line):
            # Extract the part before | or ｜
            parts = re.split(r'[|｜]', line)
            if parts:
                jp_part = parts[0].strip()
                # Remove furigana (hiragana) - keep only kanji
                # Japanese names typically use kanji, furigana is small hiragana
                kanji_only = re.sub(r'[\u3040-\u309f]', '', jp_part)  # Remove hiragana
                kanji_only = re.sub(r'\s+', '', kanji_only)  # Remove spaces
                if kanji_only and len(kanji_only) >= 2:
                    return kanji_only

            # Fallback: extract any kanji sequence
            match = re.search(r'([\u4e00-\u9fff]{2,})', line)
            if match:
                return match.group(1)

    return None


async def crawl_anime_characters_page(page, anime_title_korean):
    """Crawl anime character list page and extract character links"""
    # Try different URL patterns
    urls_to_try = [
        f"https://namu.wiki/w/{quote(anime_title_korean)}/등장인물",
        f"https://namu.wiki/w/{quote(anime_title_korean)}",
    ]

    for url in urls_to_try:
        try:
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.5)

            # Check if page exists
            text = await page.evaluate("document.body.innerText")

            if "해당 문서를 찾을 수 없습니다" in text:
                continue

            # Extract character links from the page
            character_links = await page.evaluate("""
                () => {
                    const links = [];
                    const seen = new Set();

                    // Common non-character words to filter out
                    const blacklist = [
                        '소설', '만화', '영역', '애니', '게임', '시리즈', '목차', '개요',
                        '설정', '줄거리', '등장인물', '비판', '논란', '미디어', '기타',
                        '사변', '회전', '고전', '전개', '인물', '관계', '행적', '능력',
                        '평가', '여담', '각주', '외부', '링크', '분류', '편집', '역사'
                    ];

                    document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                        const href = a.getAttribute('href');
                        const text = a.innerText.trim();

                        // Skip if already seen
                        if (seen.has(text)) return;

                        // Filter for likely character names (Korean text, 2-15 chars)
                        if (!/^[가-힣\\s]{2,15}$/.test(text)) return;
                        if (text.includes('/')) return;

                        // Skip blacklisted words
                        for (const word of blacklist) {
                            if (text.includes(word)) return;
                        }

                        // Skip if href contains non-character patterns
                        if (href.includes('/분류:') || href.includes('#')) return;

                        // Likely a character name - has space and 3+ syllables
                        if (text.includes(' ') && text.length >= 4) {
                            seen.add(text);
                            links.push({href: href, text: text});
                        }
                    });
                    return links;
                }
            """)

            # Also extract mappings directly from page content
            mappings = extract_character_mappings(text)

            return {'links': character_links, 'mappings': mappings}

        except Exception as e:
            print(f"  Error: {e}")
            continue

    return {'links': [], 'mappings': {}}


def extract_character_mappings(text):
    """Extract Korean name -> Japanese name mappings from page text"""
    mappings = {}

    # Look for patterns like:
    # 한글이름 (日本語名, English Name)
    # 日本語名｜한글이름

    # Pattern 1: Name rows in character info boxes
    # 고죠 사토루 \n 五条悟｜Satoru Gojo
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        # Check if this line contains Japanese + English
        if re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+.*[|｜].*[A-Za-z]', line):
            # Extract Japanese and English
            match = re.match(r'([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\s]+)[|｜]\s*([A-Za-z\s]+)', line)
            if match:
                japanese = match.group(1).strip()
                english = match.group(2).strip()

                # Look for Korean name in previous lines
                for j in range(max(0, i-3), i):
                    prev_line = lines[j].strip()
                    # Check if it's a Korean name (mostly Korean characters)
                    if re.match(r'^[가-힣\s]+$', prev_line) and len(prev_line) >= 2:
                        korean = prev_line
                        mappings[japanese] = korean
                        break

    return mappings


async def crawl_character_page_for_mapping(page, korean_name):
    """Crawl individual character page and extract Japanese name"""
    url = f"https://namu.wiki/w/{quote(korean_name)}"

    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.3)

        # Check if page exists
        text = await page.evaluate("document.body.innerText")

        if "해당 문서를 찾을 수 없습니다" in text:
            return None

        # Extract Japanese name
        japanese_name = extract_japanese_name(text, korean_name)
        return japanese_name

    except Exception as e:
        print(f"    Error: {e}")
        return None


async def main():
    """Main crawling function"""
    from playwright.async_api import async_playwright

    print("=" * 80)
    print("Namuwiki Character Korean Names Crawler (Playwright)")
    print("나무위키 캐릭터 한국어 이름 크롤러")
    print("=" * 80)

    # Get characters to process
    characters = get_characters_without_korean_names(limit=MAX_CHARACTERS)
    print(f"\nFound {len(characters)} characters to process")

    if not characters:
        print("No characters need Korean names!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        success_count = 0
        processed_anime = set()
        all_mappings = {}  # japanese_name -> korean_name

        for i, char in enumerate(characters):
            char_id = char['id']
            name_full = char['name_full']
            name_native = char['name_native']
            title_korean = char['title_korean']

            print(f"\n[{i+1}/{len(characters)}] {name_full} ({name_native})")
            print(f"  Anime: {title_korean}")

            # Check if we already have a mapping for this Japanese name
            if name_native in all_mappings:
                korean_name = all_mappings[name_native]
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                print(f"  ✓ Cached: {korean_name}")
                success_count += 1
                continue

            # Try crawling anime character page first (more efficient)
            if title_korean not in processed_anime:
                print(f"  Crawling anime page: {title_korean}/등장인물")
                result = await crawl_anime_characters_page(page, title_korean)
                processed_anime.add(title_korean)

                character_links = result.get('links', [])
                print(f"  Found {len(character_links)} character links")

                # Visit each character page to get japanese name mapping
                for link in character_links[:30]:  # Limit to first 30 characters
                    kr_name = link['text']

                    # Skip if already mapped
                    if any(v == kr_name for v in all_mappings.values()):
                        continue

                    jp_name = await crawl_character_page_for_mapping(page, kr_name)

                    if jp_name:
                        all_mappings[jp_name] = kr_name
                        print(f"    {kr_name} -> {jp_name}")

                        # Update database
                        updated = db.execute_update("""
                            UPDATE character
                            SET name_korean = ?
                            WHERE name_native = ? AND name_korean IS NULL
                        """, (kr_name, jp_name))

                    await asyncio.sleep(REQUEST_DELAY)

            # Check if current character was updated
            if name_native in all_mappings:
                korean_name = all_mappings[name_native]
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                print(f"  ✓ {name_full}: {korean_name}")
                success_count += 1
            else:
                # Check if character now has Korean name
                result = db.execute_query(
                    "SELECT name_korean FROM character WHERE id = ?",
                    (char_id,),
                    fetch_one=True
                )

                if result and result['name_korean']:
                    print(f"  ✓ Already updated: {result['name_korean']}")
                    success_count += 1
                else:
                    print(f"  ✗ Not found")

        await browser.close()

    # Final statistics
    print(f"\n{'='*80}")
    print("Crawling Complete!")
    print(f"{'='*80}")
    print(f"Mappings found: {len(all_mappings)}")

    # Get updated stats
    total = db.execute_query("SELECT COUNT(*) as c FROM character", fetch_one=True)['c']
    with_korean = db.execute_query(
        "SELECT COUNT(*) as c FROM character WHERE name_korean IS NOT NULL",
        fetch_one=True
    )['c']

    print(f"Total characters: {total:,}")
    print(f"With Korean names: {with_korean:,} ({with_korean/total*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
