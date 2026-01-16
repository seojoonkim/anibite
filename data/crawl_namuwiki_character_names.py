"""
Crawl character Korean names from Namuwiki
나무위키에서 캐릭터 한국어 이름 크롤링
"""
import sys
import os
import time
import re
import urllib.parse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# Import after path setup
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install requests beautifulsoup4")
    sys.exit(1)


# Configuration
NAMUWIKI_BASE_URL = "https://namu.wiki/w/"
REQUEST_DELAY = 2.0  # 2 seconds between requests (robots.txt compliance)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
MAX_CHARACTERS = 10  # None = all, or set to number for testing (e.g., 100)


def get_characters_to_crawl(limit=None):
    """
    Get characters that need Korean names
    한국어 이름이 필요한 캐릭터 조회
    """
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
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra', 'Background Character')
          AND c.name_full NOT LIKE 'Narrator%'
          AND c.name_full NOT LIKE 'Unknown%'
          AND a.title_korean IS NOT NULL
        ORDER BY c.favourites DESC, CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END
    """

    if limit:
        query += f" LIMIT {limit}"

    return db.execute_query(query)


def build_namuwiki_urls(character_name, name_native, anime_title_korean, anime_title_romaji):
    """
    Build possible Namuwiki URLs for a character
    캐릭터에 대한 나무위키 URL 후보 생성
    """
    urls = []

    # 1. First try with native name (Japanese/Chinese characters) - most likely to work
    if name_native:
        name_native_clean = name_native.strip()

        if anime_title_korean:
            # Try: 일본어이름(애니제목)
            urls.append(f"{name_native_clean}({anime_title_korean})")

        # Try: 일본어이름 alone
        urls.append(name_native_clean)

    # 2. Try with English name as fallback
    char_name_clean = character_name.strip()

    if anime_title_korean:
        # Try: 캐릭터명(애니제목)
        urls.append(f"{char_name_clean}({anime_title_korean})")

    # Try: 캐릭터명 alone
    urls.append(char_name_clean)

    # Encode URLs
    encoded_urls = [NAMUWIKI_BASE_URL + urllib.parse.quote(url) for url in urls]

    return encoded_urls


def extract_korean_name(html_content, character_name_full):
    """
    Extract Korean name from Namuwiki HTML
    나무위키 HTML에서 한국어 이름 추출
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Method 1: Look for Korean name in first paragraph
        paragraphs = soup.find_all('div', class_='wiki-paragraph')

        for para in paragraphs[:3]:  # Check first 3 paragraphs
            text = para.get_text()

            # Pattern 1: "한글이름 (English Name, ...)"
            pattern1 = r'([가-힣\s]{2,20})\s*\([^)]*' + re.escape(character_name_full)
            match = re.search(pattern1, text, re.IGNORECASE)
            if match:
                korean_name = match.group(1).strip()
                if validate_korean_name(korean_name):
                    return korean_name

            # Pattern 2: "English Name (한글이름, ...)"
            pattern2 = re.escape(character_name_full) + r'\s*\(([가-힣\s]{2,20})[,)]'
            match = re.search(pattern2, text, re.IGNORECASE)
            if match:
                korean_name = match.group(1).strip()
                if validate_korean_name(korean_name):
                    return korean_name

            # Pattern 3: Look for first standalone Korean name after character name mention
            if character_name_full.lower() in text.lower():
                # Find Korean text after character name
                idx = text.lower().find(character_name_full.lower())
                remaining = text[idx:idx+200]  # Check next 200 chars

                korean_pattern = r'([가-힣\s]{2,20})'
                matches = re.findall(korean_pattern, remaining)
                for korean_name in matches:
                    korean_name = korean_name.strip()
                    if validate_korean_name(korean_name) and len(korean_name) >= 2:
                        return korean_name

        # Method 2: Look in info table (infobox)
        infobox = soup.find('table', class_='wiki-table')
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                text = row.get_text()
                # Look for "이름", "한국명", "본명" labels
                if any(label in text for label in ['이름', '한국명', '본명', '성명']):
                    korean_pattern = r'([가-힣\s]{2,20})'
                    matches = re.findall(korean_pattern, text)
                    for korean_name in matches:
                        korean_name = korean_name.strip()
                        if validate_korean_name(korean_name):
                            return korean_name

    except Exception as e:
        print(f"  Error parsing HTML: {e}")

    return None


def validate_korean_name(name):
    """
    Validate if extracted text is a valid Korean name
    추출된 텍스트가 유효한 한국어 이름인지 검증
    """
    if not name or len(name) < 2:
        return False

    # Must be mostly Korean characters
    korean_chars = len(re.findall(r'[가-힣]', name))
    if korean_chars < len(name) * 0.7:  # At least 70% Korean
        return False

    # Filter out common false positives
    blacklist = [
        '등장인물', '주인공', '캐릭터', '애니메이션', '만화', '작품', '시리즈',
        '목차', '개요', '설명', '특징', '성격', '외모', '능력', '관계',
        '나무위키', '위키', '문서', '페이지', '내용', '항목', '참고'
    ]

    for word in blacklist:
        if word in name:
            return False

    return True


def fetch_namuwiki_page(url):
    """
    Fetch Namuwiki page with proper headers
    나무위키 페이지 가져오기 (헤더 포함)
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.RequestException as e:
        print(f"  Request error: {e}")
        return None


def crawl_character_korean_name(character):
    """
    Crawl Korean name for a single character
    단일 캐릭터에 대해 한국어 이름 크롤링
    """
    char_id, name_full, name_native, favourites, title_korean, title_romaji, role = character

    print(f"\n[{char_id}] {name_full} ({name_native or 'no native name'})")
    print(f"  Anime: {title_korean or title_romaji}")
    print(f"  Favourites: {favourites:,} | Role: {role}")

    # Build URLs to try
    urls = build_namuwiki_urls(name_full, name_native, title_korean, title_romaji)

    print(f"  Trying {len(urls)} URL(s)...")

    for i, url in enumerate(urls):
        print(f"  [{i+1}/{len(urls)}] {url}")

        # Fetch page
        html = fetch_namuwiki_page(url)

        if html:
            # Extract Korean name
            korean_name = extract_korean_name(html, name_full)

            if korean_name:
                print(f"  ✓ Found: {korean_name}")

                # Update database
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )

                return korean_name

        # Rate limiting
        time.sleep(REQUEST_DELAY)

    print(f"  ✗ Not found")
    return None


def update_crawl_meta(total_crawled, success_count):
    """
    Update crawl_meta table with progress
    크롤링 진행 상황을 crawl_meta 테이블에 업데이트
    """
    timestamp = datetime.now().isoformat()

    # Update total characters with Korean names
    db.execute_update("""
        INSERT OR REPLACE INTO crawl_meta (key, value, updated_at)
        VALUES ('characters_with_korean_name', ?, ?)
    """, (str(success_count), timestamp))

    # Update last crawl time
    db.execute_update("""
        INSERT OR REPLACE INTO crawl_meta (key, value, updated_at)
        VALUES ('last_character_name_crawl', ?, ?)
    """, (timestamp, timestamp))

    # Update progress
    db.execute_update("""
        INSERT OR REPLACE INTO crawl_meta (key, value, updated_at)
        VALUES ('character_name_crawl_progress', ?, ?)
    """, (f"{total_crawled}/47557", timestamp))


def main():
    """Main crawling function"""

    print("=" * 80)
    print("Namuwiki Character Korean Names Crawler")
    print("나무위키 캐릭터 한국어 이름 크롤러")
    print("=" * 80)

    # Get characters to crawl
    print(f"\nFetching characters to crawl (limit: {MAX_CHARACTERS or 'all'})...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS)

    print(f"Found {len(characters)} characters to process")

    if len(characters) == 0:
        print("No characters need Korean names!")
        return

    # Confirm before starting (skip for small batches)
    if not MAX_CHARACTERS or MAX_CHARACTERS > 500:
        print(f"\n⚠️  This will crawl {len(characters)} characters")
        print(f"   Estimated time: {len(characters) * REQUEST_DELAY / 3600:.1f} hours")
        confirm = input("\nContinue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return

    # Start crawling
    print(f"\nStarting crawl...")
    print(f"Rate limit: {REQUEST_DELAY} seconds per request")
    print("=" * 80)

    success_count = 0
    start_time = time.time()

    for idx, character in enumerate(characters):
        print(f"\n[{idx+1}/{len(characters)}]", end=" ")

        korean_name = crawl_character_korean_name(character)

        if korean_name:
            success_count += 1

        # Update meta every 10 characters
        if (idx + 1) % 10 == 0:
            update_crawl_meta(idx + 1, success_count)

            # Progress report
            elapsed = time.time() - start_time
            rate = success_count / (idx + 1) * 100
            print(f"\n{'='*80}")
            print(f"Progress: {idx+1}/{len(characters)} ({(idx+1)/len(characters)*100:.1f}%)")
            print(f"Success: {success_count}/{idx+1} ({rate:.1f}%)")
            print(f"Elapsed: {elapsed/60:.1f} minutes")
            print(f"{'='*80}")

    # Final update
    update_crawl_meta(len(characters), success_count)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n\n{'='*80}")
    print("Crawling Complete!")
    print(f"{'='*80}")
    print(f"Total processed: {len(characters)}")
    print(f"Successful: {success_count} ({success_count/len(characters)*100:.1f}%)")
    print(f"Failed: {len(characters) - success_count}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
