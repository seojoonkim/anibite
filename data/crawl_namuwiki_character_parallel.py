"""
Parallel Namuwiki Character Korean Name Crawler
나무위키 캐릭터 한국어 이름 병렬 크롤러

5개 병렬 처리, 10개마다 진행상황 알림
"""
import sys
import os
import time
import re
import urllib.parse
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install requests beautifulsoup4")
    sys.exit(1)


# Configuration
NAMUWIKI_BASE_URL = "https://namu.wiki/w/"
REQUEST_DELAY = 1.5  # 1.5 seconds between requests per worker
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
MAX_WORKERS = 5  # 5개 병렬 처리
MAX_CHARACTERS = None  # None = 전체, 숫자 = 테스트용 제한

# Thread-safe counters
lock = threading.Lock()
processed_count = 0
success_count = 0
last_report_count = 0


def log(msg, flush=True):
    """Thread-safe logging with flush"""
    print(msg, flush=flush)


def get_characters_to_crawl(limit=None):
    """한국어 이름이 필요한 캐릭터 조회"""
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
    """캐릭터에 대한 나무위키 URL 후보 생성"""
    urls = []

    # 1. Native name (Japanese/Chinese) - most likely
    if name_native:
        name_native_clean = name_native.strip()
        if anime_title_korean:
            urls.append(f"{name_native_clean}({anime_title_korean})")
        urls.append(name_native_clean)

    # 2. English name as fallback
    char_name_clean = character_name.strip()
    if anime_title_korean:
        urls.append(f"{char_name_clean}({anime_title_korean})")
    urls.append(char_name_clean)

    return [NAMUWIKI_BASE_URL + urllib.parse.quote(url) for url in urls]


def validate_korean_name(name):
    """한국어 이름 유효성 검증"""
    if not name or len(name) < 2:
        return False

    korean_chars = len(re.findall(r'[가-힣]', name))
    if korean_chars < len(name) * 0.7:
        return False

    blacklist = [
        '등장인물', '주인공', '캐릭터', '애니메이션', '만화', '작품', '시리즈',
        '목차', '개요', '설명', '특징', '성격', '외모', '능력', '관계',
        '나무위키', '위키', '문서', '페이지', '내용', '항목', '참고'
    ]

    for word in blacklist:
        if word in name:
            return False

    return True


def extract_korean_name(html_content, character_name_full):
    """나무위키 HTML에서 한국어 이름 추출"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Method 1: First paragraphs
        paragraphs = soup.find_all('div', class_='wiki-paragraph')

        for para in paragraphs[:3]:
            text = para.get_text()

            # Pattern 1: "한글이름 (English Name)"
            pattern1 = r'([가-힣\s]{2,20})\s*\([^)]*' + re.escape(character_name_full)
            match = re.search(pattern1, text, re.IGNORECASE)
            if match:
                korean_name = match.group(1).strip()
                if validate_korean_name(korean_name):
                    return korean_name

            # Pattern 2: "English Name (한글이름)"
            pattern2 = re.escape(character_name_full) + r'\s*\(([가-힣\s]{2,20})[,)]'
            match = re.search(pattern2, text, re.IGNORECASE)
            if match:
                korean_name = match.group(1).strip()
                if validate_korean_name(korean_name):
                    return korean_name

            # Pattern 3: Korean name after character mention
            if character_name_full.lower() in text.lower():
                idx = text.lower().find(character_name_full.lower())
                remaining = text[idx:idx+200]

                korean_pattern = r'([가-힣\s]{2,20})'
                matches = re.findall(korean_pattern, remaining)
                for korean_name in matches:
                    korean_name = korean_name.strip()
                    if validate_korean_name(korean_name) and len(korean_name) >= 2:
                        return korean_name

        # Method 2: Info table
        infobox = soup.find('table', class_='wiki-table')
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                text = row.get_text()
                if any(label in text for label in ['이름', '한국명', '본명', '성명']):
                    korean_pattern = r'([가-힣\s]{2,20})'
                    matches = re.findall(korean_pattern, text)
                    for korean_name in matches:
                        korean_name = korean_name.strip()
                        if validate_korean_name(korean_name):
                            return korean_name

    except Exception as e:
        pass

    return None


def fetch_namuwiki_page(url):
    """나무위키 페이지 가져오기"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except requests.RequestException:
        return None


def crawl_single_character(character, total_count):
    """단일 캐릭터 크롤링 (worker)"""
    global processed_count, success_count, last_report_count

    char_id, name_full, name_native, favourites, title_korean, title_romaji, role = character

    urls = build_namuwiki_urls(name_full, name_native, title_korean, title_romaji)
    korean_name = None

    for url in urls:
        html = fetch_namuwiki_page(url)

        if html:
            korean_name = extract_korean_name(html, name_full)
            if korean_name:
                # Update database
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                break

        time.sleep(REQUEST_DELAY)

    # Update counters (thread-safe)
    with lock:
        processed_count += 1
        current_processed = processed_count

        if korean_name:
            success_count += 1
            current_success = success_count
            log(f"✓ [{current_processed}/{total_count}] {name_full} → {korean_name}")
        else:
            current_success = success_count
            log(f"✗ [{current_processed}/{total_count}] {name_full}")

        # 10개마다 진행상황 알림
        if current_processed % 10 == 0 and current_processed > last_report_count:
            last_report_count = current_processed
            rate = current_success / current_processed * 100 if current_processed > 0 else 0
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {current_processed}/{total_count} ({current_processed/total_count*100:.1f}%)")
            log(f"   성공: {current_success}개 ({rate:.1f}%)")
            log(f"   실패: {current_processed - current_success}개")
            log(f"{'='*60}\n")

    return korean_name


def main():
    global processed_count, success_count, last_report_count

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 병렬 크롤러")
    log(f"   Workers: {MAX_WORKERS}개")
    log(f"   요청 간격: {REQUEST_DELAY}초")
    log("=" * 60)

    # Get characters
    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 발견")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    # Reset counters
    processed_count = 0
    success_count = 0
    last_report_count = 0

    log(f"\n🔄 크롤링 시작...")
    start_time = time.time()

    # Parallel execution
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for character in characters:
            future = executor.submit(crawl_single_character, character, total_count)
            futures.append(future)

        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"❌ Error: {e}")

    # Final report
    elapsed = time.time() - start_time
    log(f"\n\n{'='*60}")
    log("🎉 크롤링 완료!")
    log(f"{'='*60}")
    log(f"  총 처리: {processed_count}개")
    log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
    log(f"  실패: {processed_count - success_count}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    main()
