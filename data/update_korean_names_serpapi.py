#!/usr/bin/env python3
"""
SerpAPI를 사용한 캐릭터 한국어 이름 업데이트
- 봇 감지 없이 안정적인 구글 검색
- 병렬 처리 + 중간 저장 및 재개 지원

사용법:
    export SERPAPI_KEY="your_api_key"
    python3 data/update_korean_names_serpapi.py
"""
import sys
import os
import re
import json
import asyncio
import argparse
import sqlite3
import time
import signal
import atexit
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db
from config import DATABASE_PATH

try:
    from serpapi import GoogleSearch
except ImportError:
    print("Error: pip install google-search-results")
    sys.exit(1)


# ============================================================
# Configuration
# ============================================================
MAX_WORKERS = 5  # 동시 요청 수
REQUEST_DELAY = 0.5  # 요청 간 딜레이 (초) - SerpAPI는 봇 감지 없으므로 짧게
SAVE_EVERY = 10  # 처리 N개마다 저장
MIN_SCORE = 3  # 후보 점수 최소 기준

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_korean_serpapi_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_korean_serpapi_errors.log"

# Control flags
stop_requested = False
_global_progress = None

# API Key
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")


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


def is_valid_korean_name(text):
    """유효한 한국어 이름인지 확인"""
    if not text:
        return False
    text = text.strip()
    # 한글만 (공백 허용)
    if not re.match(r'^[가-힣]+(\s[가-힣]+)*$', text):
        return False
    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 15:
        return False
    # 블랙리스트
    blacklist = ['이름', '목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
                 '검색', '결과', '나무위키', '위키백과', '더보기', '관련', '문서',
                 '애니메이션', '만화', '게임', '소설', '작품', '시리즈', '캐릭터',
                 '공식', '정보', '프로필', '소개', '한국어', '일본어', '영어',
                 '번역', '발음', '표기', '원문', '스포일러', '줄거리']
    if text in blacklist:
        return False
    return True


def extract_korean_name_from_results(results, name_full, name_native=None):
    """SerpAPI 검색 결과에서 한국어 이름 추출"""
    candidates = {}
    name_full_lower = name_full.lower()

    def add_candidate(candidate, score, reason):
        if not is_valid_korean_name(candidate):
            return
        entry = candidates.setdefault(candidate, {"score": 0, "count": 0, "reason": reason})
        entry["score"] += score
        entry["count"] += 1
        if score >= entry.get("best_score", 0):
            entry["reason"] = reason
            entry["best_score"] = score

    # organic_results 처리
    organic = results.get("organic_results", [])
    for result in organic:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")

        # 패턴 1: 나무위키 제목에서 추출
        if "namu.wiki" in link:
            match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)', title)
            if match:
                add_candidate(match.group(1).strip(), 5, "namu_title")

            # URL에서 추출
            url_match = re.search(r'namu\.wiki/w/([가-힣%]+)', link)
            if url_match:
                try:
                    name = unquote(url_match.group(1))
                    name = re.sub(r'[\(（].*?[\)）]$', '', name).strip()
                    add_candidate(name, 5, "namu_url")
                except:
                    pass

        # 패턴 2: 위키피디아
        if "wikipedia" in link:
            match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)', title)
            if match:
                add_candidate(match.group(1).strip(), 4, "wiki_title")

        # 패턴 3: 제목에서 "한국어이름(영어이름)" 패턴
        match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)\s*[\(（]', title)
        if match and name_full_lower in title.lower():
            add_candidate(match.group(1).strip(), 4, "paren_with_english")

        # 패턴 4: snippet에서 한국어 이름 추출
        for text in [title, snippet]:
            if name_full_lower in text.lower():
                for name in re.findall(r'[가-힣]{2,12}(?:\s[가-힣]{1,12})?', text):
                    add_candidate(name, 2, "same_line")

            if name_native and name_native in text:
                for name in re.findall(r'[가-힣]{2,12}(?:\s[가-힣]{1,12})?', text):
                    add_candidate(name, 2, "native_line")

    # knowledge_graph 처리 (있는 경우)
    kg = results.get("knowledge_graph", {})
    if kg:
        kg_title = kg.get("title", "")
        match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)', kg_title)
        if match:
            add_candidate(match.group(1).strip(), 6, "knowledge_graph")

    if not candidates:
        return None, None

    best_name, meta = max(
        candidates.items(),
        key=lambda item: (item[1]["score"], item[1]["count"], -len(item[0]))
    )
    if meta["score"] < MIN_SCORE:
        return None, None
    return best_name, meta.get("reason")


def search_google(name_full, name_native, api_key):
    """SerpAPI로 구글 검색"""
    query = f'"{name_full}" 이름'

    params = {
        "q": query,
        "hl": "ko",
        "gl": "kr",
        "api_key": api_key,
        "num": 10,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            log_error(f"SerpAPI error for {name_full}: {results['error']}")
            return None, None

        korean_name, reason = extract_korean_name_from_results(results, name_full, name_native)

        # 첫 번째 검색에서 못 찾으면 일본어 이름으로 재검색
        if not korean_name and name_native:
            query2 = f'"{name_full}" "{name_native}" 이름'
            params["q"] = query2
            search2 = GoogleSearch(params)
            results2 = search2.get_dict()
            korean_name, reason = extract_korean_name_from_results(results2, name_full, name_native)

        return korean_name, reason

    except Exception as e:
        log_error(f"Search error for {name_full}: {e}")
        return None, None


def process_character(character, api_key):
    """단일 캐릭터 처리"""
    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']
    current_korean = character['name_korean']

    found_korean, reason = search_google(name_full, name_native, api_key)

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
    global _global_progress, SERPAPI_KEY, MAX_WORKERS, REQUEST_DELAY, MIN_SCORE

    parser = argparse.ArgumentParser(description="SerpAPI로 캐릭터 한국어 이름 검증/업데이트")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    parser.add_argument("--api-key", type=str, default=SERPAPI_KEY)
    args = parser.parse_args()

    MAX_WORKERS = max(1, args.workers)
    REQUEST_DELAY = max(0.1, args.delay)
    MIN_SCORE = max(1, args.min_score)
    SERPAPI_KEY = args.api_key or os.environ.get("SERPAPI_KEY", "")

    if not SERPAPI_KEY:
        print("Error: SERPAPI_KEY 환경변수를 설정하거나 --api-key 옵션을 사용하세요")
        print("  export SERPAPI_KEY='your_api_key'")
        print("  또는")
        print("  python3 update_korean_names_serpapi.py --api-key 'your_api_key'")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log("=" * 60)
    log("🔍 SerpAPI로 캐릭터 한국어 이름 업데이트")
    log(f"   Worker: {MAX_WORKERS}개")
    log(f"   딜레이: {REQUEST_DELAY}초")
    log(f"   최소 점수: {MIN_SCORE}")
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
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for i, character in enumerate(characters):
                if stop_requested:
                    break

                result = process_character(character, SERPAPI_KEY)

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
                            log(f"✓ [{processed_count}/{total_count}] {name_full}: {current_korean or '없음'} → {found_korean}")
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
                    log(f"\n{'='*50}")
                    log(f"📊 진행: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%)")
                    log(f"   찾음: {success_count}개 ({rate:.1f}%)")
                    log(f"   업데이트: {updated_count}개")
                    log(f"{'='*50}\n")

                # 딜레이
                time.sleep(REQUEST_DELAY)

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
