#!/usr/bin/env python3
"""
네이버 검색 API를 사용한 캐릭터 한국어 이름 업데이트
- 무료 (하루 25,000회)
- 한국어 검색에 최적화
- 봇 감지 없음

사용법:
    export NAVER_CLIENT_ID="your_client_id"
    export NAVER_CLIENT_SECRET="your_client_secret"
    python3 data/update_korean_names_naver.py
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
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db
from config import DATABASE_PATH


# ============================================================
# Configuration
# ============================================================
MAX_WORKERS = 10  # 동시 요청 수 (네이버는 제한 없음)
REQUEST_DELAY = 0.1  # 요청 간 딜레이 (초)
SAVE_EVERY = 50  # 처리 N개마다 저장
MIN_SCORE = 3  # 후보 점수 최소 기준

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_korean_naver_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_korean_naver_errors.log"

# Control flags
stop_requested = False
_global_progress = None

# API Keys
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")


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
    # 블랙리스트 - 검색 결과에서 흔히 나오는 단어들
    blacklist = [
        # 일반 단어
        '이름', '목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
        '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
        '검색', '결과', '나무위키', '위키백과', '더보기', '관련', '문서',
        '애니메이션', '만화', '게임', '소설', '작품', '시리즈', '캐릭터',
        '공식', '정보', '프로필', '소개', '한국어', '일본어', '영어',
        '번역', '발음', '표기', '원문', '스포일러', '줄거리', '블로그',
        '포스트', '리뷰', '후기', '정리', '요약', '내용', '추천', '인기',
        '서버', '다운로드', '무료', '유료', '링크', '사이트', '페이지',
        # 애니 제목 (캐릭터 이름이 아님)
        '진격의', '거인', '원피스', '나루토', '블리치', '귀멸의', '칼날',
        '주술회전', '체인소맨', '스파이', '패밀리', '해리', '포터',
        '하루노', '유짱', '구울', '도쿄', '헌터', '강철의', '연금술사',
        # 일반 명사
        '세계', '마법', '학교', '왕국', '제국', '전쟁', '평화', '사랑',
        '친구', '가족', '형제', '자매', '아버지', '어머니', '아들', '딸',
    ]
    if text in blacklist:
        return False
    # 한 글자 단어 제외 (공백으로 분리했을 때)
    words = text.split()
    if any(len(w) < 2 for w in words):
        return False
    return True


def clean_html(text):
    """HTML 태그 및 엔티티 제거"""
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    return text.strip()


def extract_korean_name_from_url(url):
    """나무위키 URL에서 한국어 이름 추출"""
    if "namu.wiki/w/" not in url:
        return None

    try:
        # URL에서 페이지 이름 추출
        page_name = url.split("namu.wiki/w/")[-1]
        page_name = urllib.parse.unquote(page_name)

        # 서브페이지 제거 (예: "엘런 예거/평가" -> "엘런 예거")
        if '/' in page_name:
            page_name = page_name.split('/')[0]

        # 괄호 제거 (예: "에렌 예거(진격의 거인)" -> "에렌 예거")
        page_name = re.sub(r'[\(（].*?[\)）]$', '', page_name).strip()

        # 한국어만 추출 (D. 같은 이니셜 제거)
        korean_parts = []
        for part in page_name.split():
            if re.match(r'^[가-힣]+$', part):
                korean_parts.append(part)

        if korean_parts:
            name = ' '.join(korean_parts)
            if is_valid_korean_name(name):
                return name

    except Exception:
        pass

    return None


def extract_korean_name_from_results(items, name_full, name_native=None):
    """네이버 검색 결과에서 한국어 이름 추출 (나무위키 URL 우선)"""
    candidates = {}

    def add_candidate(candidate, score, reason):
        if not is_valid_korean_name(candidate):
            return
        entry = candidates.setdefault(candidate, {"score": 0, "count": 0, "reason": reason})
        entry["score"] += score
        entry["count"] += 1
        if score >= entry.get("best_score", 0):
            entry["reason"] = reason
            entry["best_score"] = score

    for item in items:
        title = clean_html(item.get("title", ""))
        link = item.get("link", "")

        # 1순위: 나무위키 URL에서 직접 추출 (가장 정확)
        if "namu.wiki" in link:
            url_name = extract_korean_name_from_url(link)
            if url_name:
                add_candidate(url_name, 15, "namu_url")

            # 2순위: 제목에서 추출 (URL이 영어인 경우)
            match = re.search(r'^([가-힣]{2,6}(?:\s[가-힣]{1,6})?)\s*[-\(（]', title)
            if match:
                add_candidate(match.group(1).strip(), 10, "namu_title")

        # 3순위: 위키피디아 제목
        if "wikipedia" in link:
            match = re.search(r'^([가-힣]{2,6}(?:\s[가-힣]{1,6})?)\s*[-\(（]', title)
            if match:
                add_candidate(match.group(1).strip(), 8, "wiki_title")

    if not candidates:
        return None, None

    best_name, meta = max(
        candidates.items(),
        key=lambda item: (item[1]["score"], item[1]["count"], -len(item[0]))
    )
    # 점수 기준: 나무위키 URL(15) 또는 나무위키 제목(10) 이상만 통과
    if meta["score"] < 8:
        return None, None
    return best_name, meta.get("reason")


def search_naver(name_full, name_native, client_id, client_secret):
    """네이버 검색 API 호출"""
    # 일본어 이름을 포함해서 정확도 향상
    if name_native:
        query = f'"{name_native}" 나무위키'
    else:
        query = f'"{name_full}" 나무위키 애니메이션'

    encoded_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/webkr.json?query={encoded_query}&display=10"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        response = urllib.request.urlopen(request, timeout=10)
        response_body = response.read().decode('utf-8')
        result = json.loads(response_body)
        items = result.get("items", [])

        korean_name, reason = extract_korean_name_from_results(items, name_full, name_native)

        # 첫 번째 검색에서 못 찾으면 영어 이름으로 재검색
        if not korean_name:
            query2 = f'"{name_full}" 나무위키'
            encoded_query2 = urllib.parse.quote(query2)
            url2 = f"https://openapi.naver.com/v1/search/webkr.json?query={encoded_query2}&display=10"

            request2 = urllib.request.Request(url2)
            request2.add_header("X-Naver-Client-Id", client_id)
            request2.add_header("X-Naver-Client-Secret", client_secret)

            response2 = urllib.request.urlopen(request2, timeout=10)
            response_body2 = response2.read().decode('utf-8')
            result2 = json.loads(response_body2)
            items2 = result2.get("items", [])

            korean_name, reason = extract_korean_name_from_results(items2, name_full, name_native)

        return korean_name, reason

    except urllib.error.HTTPError as e:
        if e.code == 429:
            log_error(f"Rate limit exceeded for {name_full}")
        else:
            log_error(f"HTTP error for {name_full}: {e.code}")
        return None, None
    except Exception as e:
        log_error(f"Search error for {name_full}: {e}")
        return None, None


def process_character(character, client_id, client_secret):
    """단일 캐릭터 처리"""
    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']
    current_korean = character['name_korean']

    found_korean, reason = search_naver(name_full, name_native, client_id, client_secret)

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
    global _global_progress, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, MAX_WORKERS, REQUEST_DELAY, MIN_SCORE

    parser = argparse.ArgumentParser(description="네이버 검색 API로 캐릭터 한국어 이름 검증/업데이트")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    parser.add_argument("--client-id", type=str, default=NAVER_CLIENT_ID)
    parser.add_argument("--client-secret", type=str, default=NAVER_CLIENT_SECRET)
    args = parser.parse_args()

    MAX_WORKERS = max(1, args.workers)
    REQUEST_DELAY = max(0.05, args.delay)
    MIN_SCORE = max(1, args.min_score)
    NAVER_CLIENT_ID = args.client_id or os.environ.get("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET = args.client_secret or os.environ.get("NAVER_CLIENT_SECRET", "")

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("Error: 네이버 API 키가 필요합니다")
        print("  export NAVER_CLIENT_ID='your_client_id'")
        print("  export NAVER_CLIENT_SECRET='your_client_secret'")
        print("  또는")
        print("  python3 update_korean_names_naver.py --client-id 'ID' --client-secret 'SECRET'")
        print("\n발급: https://developers.naver.com → 애플리케이션 등록 → 검색 API")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log("=" * 60)
    log("🔍 네이버 검색 API로 캐릭터 한국어 이름 업데이트")
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
    log(f"   예상 시간: {total_count * REQUEST_DELAY / MAX_WORKERS / 60:.0f}분")
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
            futures = {}
            for character in characters:
                if stop_requested:
                    break
                future = executor.submit(process_character, character, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
                futures[future] = character
                time.sleep(REQUEST_DELAY)

            for future in as_completed(futures):
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
