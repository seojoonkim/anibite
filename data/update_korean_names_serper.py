#!/usr/bin/env python3
"""
Serper.dev (구글 검색 API)를 사용한 캐릭터 한국어 이름 업데이트
- 구글 검색으로 정확한 나무위키 페이지 찾기
- 봇 감지 없음, 빠른 속도

사용법:
    export SERPER_API_KEY="your_api_key"
    python3 data/update_korean_names_serper.py
"""
import sys
import os
import re
import json
import argparse
import sqlite3
import time
import signal
import atexit
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db
from config import DATABASE_PATH


# ============================================================
# Configuration
# ============================================================
MAX_WORKERS = 20  # 동시 요청 수 (병렬)
REQUEST_DELAY = 0.05  # 요청 간 딜레이 (초)
SAVE_EVERY = 100  # 처리 N개마다 저장

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_korean_serper_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_korean_serper_errors.log"

# Control flags
stop_requested = False
_global_progress = None

# API Key
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def log_error(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"processed_ids": [], "updated": {}, "same": [], "not_found": [], "errors": []}


def save_progress(progress):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"Failed to save progress: {e}")


def get_all_characters(limit=None, exclude_ids=None):
    """모든 캐릭터 조회"""
    exclude_ids = exclude_ids or []

    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.name_korean,
            c.favourites
        FROM character c
        WHERE c.name_native IS NOT NULL
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra')
          AND c.name_native != ''
          AND LENGTH(c.name_native) >= 2
          AND LENGTH(c.name_full) >= 3
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


def is_valid_character_name(name):
    """유효한 캐릭터 이름인지 확인"""
    if not name:
        return False

    # 길이 체크 (2~10자)
    clean = name.replace(' ', '')
    if len(clean) < 2 or len(clean) > 10:
        return False

    # 단어 수 체크 (1~3단어)
    words = name.split()
    if len(words) > 3:
        return False

    # 블랙리스트 - 작품 제목, 일반 문장
    blacklist = [
        # 작품 제목
        '하이큐', '데스노트', '원피스', '나루토', '블리치', '귀멸의',
        '주술회전', '체인소맨', '진격의', '거인', '헌터', '헌터',
        '강철의', '연금술사', '슈타인즈', '게이트', '가는', '연애',
        '고백받고', '싶어', '새로운', '시작', '재난', '따라해', '보자',
        # 일반 단어
        '시리즈', '등장인물', '캐릭터', '애니메이션', '만화', '소설',
    ]

    for word in blacklist:
        if word in name:
            return False

    return True


def extract_korean_name_from_url(url):
    """나무위키 URL에서 한국어 이름 추출"""
    if "namu.wiki/w/" not in url:
        return None

    try:
        # URL에서 페이지 이름 추출
        page_name = url.split("namu.wiki/w/")[-1]
        # 쿼리 파라미터 제거
        if "?" in page_name:
            page_name = page_name.split("?")[0]
        page_name = unquote(page_name)

        # 캐릭터 페이지가 아닌 것 필터링
        skip_patterns = ['/등장인물', '/시리즈', '/애니메이션', '/만화', '/게임']
        for pattern in skip_patterns:
            if pattern in page_name:
                return None

        # 서브페이지 제거 (예: "엘런 예거/평가" -> "엘런 예거")
        if '/' in page_name:
            page_name = page_name.split('/')[0]

        # 괄호 제거 (예: "에렌 예거(진격의 거인)" -> "에렌 예거")
        page_name = re.sub(r'[\(（].*?[\)）]$', '', page_name).strip()

        # 한국어 이름 추출
        # "몽키 D. 루피" -> "몽키 루피"
        korean_parts = []
        for part in page_name.split():
            if re.match(r'^[가-힣]+$', part):
                korean_parts.append(part)

        if korean_parts and len(korean_parts) >= 1:
            name = ' '.join(korean_parts)
            if is_valid_character_name(name):
                return name

    except Exception:
        pass

    return None


def extract_korean_name_from_title(title):
    """제목에서 한국어 이름 추출"""
    # "몽키 D. 루피" 또는 "엘런 예거" 패턴
    match = re.match(r'^([가-힣]+(?:\s[가-힣A-Z\.]+)*)', title)
    if match:
        name = match.group(1).strip()
        # 한국어 부분만 추출
        korean_parts = []
        for part in name.split():
            if re.match(r'^[가-힣]+$', part):
                korean_parts.append(part)
        if korean_parts:
            result = ' '.join(korean_parts)
            if is_valid_character_name(result):
                return result
    return None


def search_serper(name_full, name_native, api_key):
    """Serper.dev로 구글 검색"""
    # 일본어 이름으로 검색 (더 정확)
    query = f'"{name_native}" 나무위키' if name_native else f'"{name_full}" 나무위키 캐릭터'

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "kr", "hl": "ko", "num": 5},
            timeout=10
        )

        if response.status_code != 200:
            log_error(f"Serper API error {response.status_code} for {name_full}")
            return None, None

        results = response.json()
        organic = results.get("organic", [])

        # 나무위키 결과에서 한국어 이름 추출
        for item in organic:
            link = item.get("link", "")
            title = item.get("title", "")

            if "namu.wiki" in link:
                # 1순위: URL에서 추출
                url_name = extract_korean_name_from_url(link)
                if url_name:
                    return url_name, "url"

                # 2순위: 제목에서 추출
                title_name = extract_korean_name_from_title(title)
                if title_name:
                    return title_name, "title"

        # 영어 이름으로 재검색
        if name_native:
            query2 = f'"{name_full}" 나무위키'
            response2 = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query2, "gl": "kr", "hl": "ko", "num": 5},
                timeout=10
            )

            if response2.status_code == 200:
                results2 = response2.json()
                for item in results2.get("organic", []):
                    link = item.get("link", "")
                    title = item.get("title", "")

                    if "namu.wiki" in link:
                        url_name = extract_korean_name_from_url(link)
                        if url_name:
                            return url_name, "url_en"

                        title_name = extract_korean_name_from_title(title)
                        if title_name:
                            return title_name, "title_en"

        return None, None

    except Exception as e:
        log_error(f"Search error for {name_full}: {e}")
        return None, None


def process_character(character, api_key):
    """단일 캐릭터 처리"""
    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']
    current_korean = character['name_korean']

    # 기존 값이 유효한 캐릭터 이름이면 건드리지 않음
    if current_korean and is_valid_character_name(current_korean):
        return {
            "id": char_id,
            "name_full": name_full,
            "name_native": name_native,
            "current_korean": current_korean,
            "found_korean": current_korean,  # 기존 값 유지
            "reason": "existing_valid"
        }

    found_korean, reason = search_serper(name_full, name_native, api_key)

    return {
        "id": char_id,
        "name_full": name_full,
        "name_native": name_native,
        "current_korean": current_korean,
        "found_korean": found_korean,
        "reason": reason
    }


def emergency_save():
    """긴급 저장"""
    global _global_progress
    if _global_progress:
        try:
            save_progress(_global_progress)
            log("💾 긴급 저장 완료")
        except Exception as e:
            log_error(f"Emergency save failed: {e}")


def handle_signal(signum, frame):
    global stop_requested
    stop_requested = True
    log(f"⚠ 종료 신호 수신. 저장 후 종료합니다.")
    emergency_save()
    sys.exit(0)


atexit.register(emergency_save)


def main():
    global _global_progress, SERPER_API_KEY, MAX_WORKERS, REQUEST_DELAY

    parser = argparse.ArgumentParser(description="Serper.dev로 캐릭터 한국어 이름 검증/업데이트")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--api-key", type=str, default=SERPER_API_KEY)
    args = parser.parse_args()

    MAX_WORKERS = max(1, args.workers)
    REQUEST_DELAY = max(0.1, args.delay)
    SERPER_API_KEY = args.api_key or os.environ.get("SERPER_API_KEY", "")

    if not SERPER_API_KEY:
        print("Error: SERPER_API_KEY 환경변수를 설정하거나 --api-key 옵션을 사용하세요")
        print("  export SERPER_API_KEY='your_api_key'")
        print("  또는")
        print("  python3 update_korean_names_serper.py --api-key 'your_api_key'")
        print("\n발급: https://serper.dev")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log("=" * 60)
    log("🔍 Serper.dev (구글 검색)로 캐릭터 한국어 이름 업데이트")
    log(f"   Worker: {MAX_WORKERS}개")
    log(f"   딜레이: {REQUEST_DELAY}초")
    log("=" * 60)

    progress = load_progress()
    _global_progress = progress
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행 상황:")
        log(f"   처리됨: {len(processed_ids)}개")
        log(f"   업데이트: {len(progress.get('updated', {}))}개")
        log(f"   동일: {len(progress.get('same', []))}개")
        log(f"   못찾음: {len(progress.get('not_found', []))}개")

    log("\n📋 캐릭터 조회 중...")
    characters = get_all_characters(limit=args.limit, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    log(f"\n🔄 검색 시작...")
    start_time = datetime.now()

    # DB 연결
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=60.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    processed_ids_set = set(processed_ids)
    same_ids = set(progress.get("same", []))
    not_found_ids = set(progress.get("not_found", []))
    updated_map = progress.get("updated", {})
    errors = progress.get("errors", [])

    processed_count = 0
    success_count = 0
    updated_count = 0

    try:
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 모든 작업 제출
            future_to_char = {
                executor.submit(process_character, char, SERPER_API_KEY): char
                for char in characters
            }

            for future in as_completed(future_to_char):
                if stop_requested:
                    break

                try:
                    result = future.result(timeout=30)
                except Exception as e:
                    log_error(f"Future error: {e}")
                    continue

                processed_count += 1
                char_id = result["id"]
                name_full = result["name_full"]
                current_korean = result["current_korean"]
                found_korean = result["found_korean"]
                reason = result.get("reason")

                if found_korean:
                    success_count += 1
                    if current_korean != found_korean:
                        try:
                            cursor.execute(
                                "UPDATE character SET name_korean = ? WHERE id = ?",
                                (found_korean, char_id)
                            )
                            updated_count += 1
                            updated_map[str(char_id)] = {
                                "name": name_full,
                                "old": current_korean,
                                "new": found_korean,
                                "reason": reason
                            }
                            log(f"✓ [{processed_count}/{total_count}] {name_full}: {current_korean or 'NULL'} → {found_korean}")
                        except Exception as e:
                            errors.append({"id": char_id, "name": name_full, "error": str(e)})
                            log_error(f"DB update failed for {char_id} {name_full}: {e}")
                    else:
                        same_ids.add(char_id)
                else:
                    not_found_ids.add(char_id)

                processed_ids_set.add(char_id)

                # 주기적 저장
                if processed_count % SAVE_EVERY == 0:
                    conn.commit()
                    progress["processed_ids"] = list(processed_ids_set)
                    progress["same"] = list(same_ids)
                    progress["not_found"] = list(not_found_ids)
                    progress["updated"] = updated_map
                    progress["errors"] = errors
                    save_progress(progress)

                    rate = success_count / processed_count * 100 if processed_count > 0 else 0
                    elapsed = (datetime.now() - start_time).total_seconds()
                    speed = processed_count / elapsed * 60 if elapsed > 0 else 0
                    eta = (total_count - processed_count) / speed if speed > 0 else 0

                    log(f"\n{'='*50}")
                    log(f"📊 진행: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%)")
                    log(f"   찾음: {success_count}개 ({rate:.1f}%)")
                    log(f"   업데이트: {updated_count}개")
                    log(f"   속도: {speed:.0f}개/분, 남은 시간: {eta:.0f}분")
                    log(f"{'='*50}\n")

        conn.commit()

    finally:
        conn.close()

    # 최종 저장
    progress["processed_ids"] = list(processed_ids_set)
    progress["same"] = list(same_ids)
    progress["not_found"] = list(not_found_ids)
    progress["updated"] = updated_map
    progress["errors"] = errors
    save_progress(progress)

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n{'='*60}")
    log("🎉 완료!")
    log(f"  처리: {processed_count}개")
    log(f"  찾음: {success_count}개 ({success_count/max(processed_count,1)*100:.1f}%)")
    log(f"  업데이트: {updated_count}개")
    log(f"  시간: {elapsed/60:.1f}분")
    log(f"  속도: {processed_count/max(elapsed,1)*60:.1f}개/분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    main()
