#!/usr/bin/env python3
"""
위키피디아 언어링크를 이용한 일본어→한국어 캐릭터 이름 매칭
일본어 위키피디아 API 활용, 가장 정확하고 빠름
"""
import sys
import os
import re
import time
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db


# Configuration
MAX_WORKERS = 10  # 위키피디아 API는 더 많은 병렬 가능
MAX_CHARACTERS = 200  # None = 전체, 테스트용
BATCH_SIZE = 50  # API 배치 크기

# Global counters
processed_count = 0
success_count = 0
lock = threading.Lock()


def log(msg):
    print(msg, flush=True)


def get_characters_to_match(limit=None):
    """일본어 이름이 있고 한국어 이름이 없는 캐릭터"""
    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native
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


def get_korean_name_from_wikipedia(jp_name):
    """
    위키피디아 언어링크로 한국어 이름 가져오기

    Args:
        jp_name: 일본어 이름 (예: 夜神月)

    Returns:
        한국어 위키피디아 페이지 제목 또는 None
    """
    url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "langlinks",
        "titles": jp_name,
        "lllang": "ko",
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page_id in pages:
            if page_id == "-1":
                continue
            langlinks = pages[page_id].get("langlinks", [])
            if langlinks:
                return langlinks[0]["*"]

    except Exception as e:
        pass

    return None


USER_AGENT = "AnipassBot/1.0 (https://github.com/anipass; contact@anipass.app)"


def get_korean_names_batch(jp_names):
    """
    배치로 여러 일본어 이름의 한국어 매칭 가져오기

    Args:
        jp_names: 일본어 이름 리스트 (최대 50개)

    Returns:
        {일본어이름: 한국어이름} 딕셔너리
    """
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

    headers = {
        "User-Agent": USER_AGENT,
    }

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

                # normalized 처리 (API가 제목을 정규화할 수 있음)
                original_title = normalized.get(title, title)
                results[original_title] = korean_name

    except Exception as e:
        log(f"Error in batch request: {e}")

    return results


def is_valid_korean_name(text):
    """한글 캐릭터 이름 유효성"""
    if not text:
        return False

    # 괄호 내용 제거
    text = re.sub(r'\s*\([^)]*\)\s*$', '', text).strip()

    # 너무 길거나 비이름 패턴 제외
    if len(text) > 20:
        return False

    # 한글이 포함되어 있어야 함
    if not re.search(r'[가-힣]', text):
        return False

    # 카테고리나 특수 페이지 제외
    blacklist = ['목록', '등장인물', '작품', '시리즈', '분류', '캐릭터', '애니메이션']
    for word in blacklist:
        if word in text:
            return False

    return True


def process_batch(characters):
    """캐릭터 배치 처리"""
    global processed_count, success_count

    # 일본어 이름 리스트
    jp_names = [char['name_native'] for char in characters]
    char_map = {char['name_native']: char for char in characters}

    # 배치 API 호출
    results = get_korean_names_batch(jp_names)

    local_success = 0

    for jp_name, korean_name in results.items():
        if jp_name in char_map and is_valid_korean_name(korean_name):
            char = char_map[jp_name]

            # 괄호 내용 제거 (예: "나루토 (만화)")
            clean_name = re.sub(r'\s*\([^)]*\)\s*$', '', korean_name).strip()

            db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (clean_name, char['id'])
            )
            local_success += 1

    with lock:
        processed_count += len(characters)
        success_count += local_success

        if local_success > 0:
            log(f"✓ Batch: {local_success}/{len(characters)} 성공")

        if processed_count % 100 == 0:
            rate = success_count / processed_count * 100 if processed_count > 0 else 0
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {processed_count} 처리")
            log(f"   성공: {success_count}개 ({rate:.1f}%)")
            log(f"{'='*60}\n")

    return local_success


def main():
    global processed_count, success_count

    log("=" * 60)
    log("🚀 위키피디아 언어링크 캐릭터 이름 매칭")
    log(f"   {MAX_WORKERS}개 병렬, 배치 크기 {BATCH_SIZE}")
    log("=" * 60)

    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_match(limit=MAX_CHARACTERS)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 발견")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0

    # 배치로 분할
    batches = []
    for i in range(0, len(characters), BATCH_SIZE):
        batches.append(characters[i:i + BATCH_SIZE])

    log(f"\n🔄 {len(batches)}개 배치 처리 시작...")
    start_time = time.time()

    # 병렬 처리
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"Error: {e}")

            # Rate limiting
            time.sleep(0.1)

    elapsed = time.time() - start_time

    log(f"\n\n{'='*60}")
    log("🎉 완료!")
    log(f"{'='*60}")
    log(f"  총 처리: {processed_count}개")
    log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    main()
