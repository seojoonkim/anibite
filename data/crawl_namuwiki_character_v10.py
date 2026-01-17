#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v10
짧은 이름 캐릭터 전용 - 애니메이션 제목과 함께 검색

예: "Jin 사무라이 참프루" → 진
"""
import sys
import os
import re
import json
import asyncio
from urllib.parse import quote, unquote
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: pip install httpx beautifulsoup4")
    sys.exit(1)


# Configuration
MAX_CONCURRENT = 10
MAX_CHARACTERS = None
REQUEST_TIMEOUT = 10

PROGRESS_FILE = Path(__file__).parent / "crawl_progress_v10.json"
ERROR_LOG_FILE = Path(__file__).parent / "crawl_errors_v10.log"

# Global
processed_count = 0
success_count = 0
lock = asyncio.Lock()
semaphore = None


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


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


def get_characters_with_anime(limit=None, exclude_ids=None):
    """애니메이션 정보와 함께 캐릭터 조회"""
    exclude_ids = exclude_ids or []

    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.favourites,
            (
                SELECT a.title_romaji
                FROM anime a
                JOIN anime_character ac ON a.id = ac.anime_id
                WHERE ac.character_id = c.id
                LIMIT 1
            ) as anime_title,
            (
                SELECT a.title_korean
                FROM anime a
                JOIN anime_character ac ON a.id = ac.anime_id
                WHERE ac.character_id = c.id
                AND a.title_korean IS NOT NULL
                LIMIT 1
            ) as anime_title_korean
        FROM character c
        WHERE c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra')
          AND c.name_native != ''
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
    if len(clean) < 1 or len(clean) > 10:  # 1글자도 허용 (짧은 이름용)
        return False
    blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '편집', '토론', '역사', '최근', '수정', '시각', '기능',
                 '작품', '시리즈', '애니', '만화', '게임', '소설', '더보기',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록']
    if text in blacklist or any(b in text for b in blacklist):
        return False
    return True


def extract_kanji(text):
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


async def fetch_page(client, url):
    """페이지 가져오기"""
    try:
        async with semaphore:
            response = await client.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.text
    except:
        pass
    return None


def extract_links_from_search(html):
    """검색 결과에서 링크 추출"""
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/w/') and '#' not in href and ':' not in href:
            links.append(href)

    return list(dict.fromkeys(links))[:30]


def is_character_document(text, name_native):
    """캐릭터 문서인지 확인 (짧은 이름용 완화된 버전)"""
    header = text[:3000]

    # 실존 인물 제외
    real_person_cats = ['남배우', '여배우', '가수', '아이돌', '출생', '데뷔']
    for cat in real_person_cats:
        if cat in header[:1000]:
            return False

    # 일본어 이름이 있으면 캐릭터일 가능성 높음
    if name_native in text[:2000]:
        return True

    # 성우 정보가 있으면 캐릭터
    if '성우' in header or 'CV' in header or 'C.V' in header:
        return True

    return False


def match_character_name(text, name_native, name_full):
    """캐릭터 이름 매칭 확인"""
    header = text[:2000]

    # 일본어 이름 직접 매칭
    if name_native in header:
        return True

    # 한자 추출해서 매칭
    target_kanji = extract_kanji(name_native)
    if target_kanji and target_kanji in header:
        return True

    # 영어 이름 매칭
    if name_full.lower() in header.lower():
        return True

    return False


def extract_korean_title(text):
    """페이지에서 한글 제목 추출"""
    lines = text.split('\n')
    for line in lines[:15]:
        line = line.strip()
        # 한글만 있는 라인
        if re.match(r'^[가-힣]+$', line) and 1 <= len(line) <= 10:
            if is_valid_korean_name(line):
                return line
    return None


async def search_with_anime(client, name_native, name_full, anime_title, anime_title_korean):
    """애니메이션 제목과 함께 검색"""

    search_terms = []

    # 1. 일본어 이름 + 한국어 애니 제목
    if anime_title_korean:
        search_terms.append(f"{name_native} {anime_title_korean}")

    # 2. 일본어 이름만
    search_terms.append(name_native)

    # 3. 영어 이름 + 영어 애니 제목
    if anime_title:
        search_terms.append(f"{name_full} {anime_title}")

    for search_term in search_terms:
        search_url = f"https://namu.wiki/Search?q={quote(search_term)}"

        html = await fetch_page(client, search_url)
        if not html:
            continue

        links = extract_links_from_search(html)

        # 한글 이름 URL 필터링
        korean_candidates = []
        for href in links:
            try:
                decoded = unquote(href.replace('/w/', ''))
                name_part = re.sub(r'\([^)]*\)$', '', decoded).strip()
                if is_valid_korean_name(name_part):
                    korean_candidates.append({'name': name_part, 'href': href})
            except:
                pass

        # 중복 제거
        seen = set()
        unique = []
        for c in korean_candidates:
            if c['name'] not in seen:
                seen.add(c['name'])
                unique.append(c)

        # 각 후보 확인
        for candidate in unique[:5]:
            korean_name = candidate['name']
            href = candidate['href']

            doc_url = f"https://namu.wiki{href}"
            doc_html = await fetch_page(client, doc_url)

            if not doc_html:
                continue

            soup = BeautifulSoup(doc_html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            if "해당 문서를 찾을 수 없습니다" in text:
                continue

            if not is_character_document(text, name_native):
                continue

            if match_character_name(text, name_native, name_full):
                title = extract_korean_title(text)
                if title:
                    return title
                return korean_name

        await asyncio.sleep(0.3)

    return None


async def process_character(client, character, total_count, progress):
    """단일 캐릭터 처리"""
    global processed_count, success_count

    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']
    anime_title = character['anime_title'] or ''
    anime_title_korean = character['anime_title_korean'] or ''

    korean_name = None

    try:
        korean_name = await search_with_anime(
            client, name_native, name_full, anime_title, anime_title_korean
        )

        if korean_name:
            db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (korean_name, char_id)
            )

    except Exception as e:
        pass

    async with lock:
        processed_count += 1
        current = processed_count

        if korean_name:
            success_count += 1
            progress["success"][str(char_id)] = korean_name
            anime_info = f" [{anime_title_korean or anime_title}]" if anime_title else ""
            log(f"✓ [{current}/{total_count}] {name_full}{anime_info} → {korean_name}")
        else:
            log(f"✗ [{current}/{total_count}] {name_full} ({name_native})")

        progress["processed_ids"].append(char_id)

        if current % 20 == 0:
            rate = success_count / current * 100 if current > 0 else 0
            log(f"\n📊 진행: {current}/{total_count} | 성공: {success_count}개 ({rate:.1f}%)\n")
            save_progress(progress)


async def main():
    global processed_count, success_count, semaphore

    log("=" * 60)
    log("🚀 나무위키 캐릭터 크롤러 v10")
    log("   짧은 이름 캐릭터 전용 - 애니메이션 제목과 함께 검색")
    log("=" * 60)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행: {len(processed_ids)}개 처리됨, 성공: {len(progress.get('success', {}))}개")

    log("\n📋 캐릭터 조회 중...")
    characters = get_characters_with_anime(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0

    log(f"\n🔄 크롤링 시작...")
    start_time = datetime.now()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        batch_size = 50
        for i in range(0, len(characters), batch_size):
            batch = characters[i:i + batch_size]

            tasks = [
                process_character(client, char, total_count, progress)
                for char in batch
            ]

            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n{'='*60}")
    log("🎉 완료!")
    log(f"  처리: {processed_count}개 | 성공: {success_count}개 ({success_count/max(processed_count,1)*100:.1f}%)")
    log(f"  시간: {elapsed/60:.1f}분 | 속도: {processed_count/max(elapsed,1)*60:.1f}개/분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
