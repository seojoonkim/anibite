#!/usr/bin/env python3
"""
구글 검색으로 모든 캐릭터의 공식 한국어 이름 업데이트/검증
- 기존 한국어 이름도 전부 재검증
- 구글 rate limit 우회 (랜덤 딜레이 + 글로벌 쿨다운)
- 병렬 처리 + 단일 writer로 DB 잠금 최소화
- 중간 저장 및 재개 지원

예: "Eren Yeager" 이름 → 엘런 예거
"""
import sys
import os
import re
import json
import asyncio
import random
import argparse
import sqlite3
import time
import signal
import atexit
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, quote_plus

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db
from config import DATABASE_PATH

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: pip install playwright && playwright install chromium")
    sys.exit(1)


# ============================================================
# Configuration - 안정적 속도 (봇 감지 우회)
# ============================================================
MAX_WORKERS = 3  # 브라우저 동시 실행 수 (안정적)
MIN_DELAY = 2.0  # 최소 딜레이 (초)
MAX_DELAY = 4.0  # 최대 딜레이 (초)
GLOBAL_MIN_INTERVAL = 1.0  # 전체 요청 간 최소 간격 (초)
PAGE_TIMEOUT = 15000  # 충분한 타임아웃
MAX_CHARACTERS = None  # None = 전체, 숫자로 제한 가능
SAVE_EVERY = 10  # 처리 N개마다 저장
SAVE_INTERVAL = 60  # N초마다 저장 (보조)
MIN_SCORE = 3  # 후보 점수 최소 기준 (높을수록 보수적)

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_all_korean_progress.json"
ERROR_LOG_FILE = Path(__file__).parent / "update_all_korean_errors.log"

# Control flags
stop_requested = False

# Global progress for emergency save
_global_progress = None
_global_progress_lock = None

# User Agent Pool - 다양한 브라우저 시뮬레이션
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


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
            json.dump(progress, f, ensure_ascii=False)
    except Exception as e:
        log_error(f"Failed to save progress: {e}")


def get_all_characters(limit=None, exclude_ids=None):
    """모든 캐릭터 조회 (한국어 이름 있는 것 포함)"""
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
    blacklist = ['이름', '목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록',
                 '검색', '결과', '나무위키', '위키백과', '더보기', '관련', '문서',
                 '애니메이션', '만화', '게임', '소설', '작품', '시리즈', '캐릭터',
                 '공식', '정보', '프로필', '소개', '한국어', '일본어', '영어',
                 '번역', '발음', '표기', '원문', '스포일러', '줄거리']
    if text in blacklist or any(b == text for b in blacklist):
        return False
    return True


def extract_korean_name_from_google(page_text, name_full, name_native=None):
    """구글 검색 결과에서 한국어 이름 추출 (점수 기반)"""
    lines = page_text.split('\n')
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

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 패턴 1: "한국어이름 - 나무위키"
        match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)\s*[-–—]\s*나무위키', line)
        if match:
            add_candidate(match.group(1).strip(), 4, "namu_title")
            continue

        # 패턴 2: "한국어이름 - 위키"
        match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)\s*[-–—]\s*위키', line)
        if match:
            add_candidate(match.group(1).strip(), 3, "wiki_title")

        # 패턴 3: 나무위키 URL (/w/한국어이름)
        match = re.search(r'namu\.wiki/w/([가-힣%]+(?:%20[가-힣%]+)*)', line)
        if match:
            try:
                name = unquote(match.group(1))
                name = re.sub(r'[\(（].*?[\)）]$', '', name).strip()
                add_candidate(name, 4, "namu_url")
            except:
                pass

        # 패턴 4: "한국어이름(영어이름)"
        match = re.search(r'^([가-힣]{2,12}(?:\s[가-힣]{1,12})?)\s*[\(（]', line)
        if match and name_full_lower in line.lower():
            add_candidate(match.group(1).strip(), 3, "paren_with_english")

        # 패턴 5: "한국어 이름: XXX"
        match = re.search(r'한국어\s*이름\s*[:：]\s*([가-힣]{2,12}(?:\s[가-힣]{1,12})?)', line)
        if match:
            add_candidate(match.group(1).strip(), 3, "korean_label")

        # 패턴 6: 영어 이름 포함 + 한국어 이름 같이 존재
        if name_full_lower in line.lower():
            for name in re.findall(r'[가-힣]{2,12}(?:\s[가-힣]{1,12})?', line):
                add_candidate(name, 2, "same_line")

        if name_native and name_native in line:
            for name in re.findall(r'[가-힣]{2,12}(?:\s[가-힣]{1,12})?', line):
                add_candidate(name, 2, "native_line")

    if not candidates:
        return None, None

    best_name, meta = max(
        candidates.items(),
        key=lambda item: (item[1]["score"], item[1]["count"], -len(item[0]))
    )
    if meta["score"] < MIN_SCORE:
        return None, None
    return best_name, meta.get("reason")


class GlobalCooldown:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._until = 0.0

    async def wait(self):
        async with self._lock:
            now = time.time()
            delay = max(0.0, self._until - now)
        if delay > 0:
            await asyncio.sleep(delay)

    async def trigger(self, seconds):
        async with self._lock:
            self._until = max(self._until, time.time() + seconds)


class GlobalRateLimiter:
    def __init__(self, min_interval):
        self.min_interval = min_interval
        self._lock = asyncio.Lock()
        self._next_time = 0.0

    async def wait(self):
        async with self._lock:
            now = time.time()
            if now < self._next_time:
                delay = self._next_time - now
                self._next_time += self.min_interval
            else:
                delay = 0.0
                self._next_time = now + self.min_interval
        if delay > 0:
            await asyncio.sleep(delay)


def build_queries(name_full, name_native):
    queries = [f'"{name_full}" 이름']
    if name_native and name_native not in name_full:
        queries.append(f'"{name_full}" "{name_native}" 이름')
    if len(queries) < 2 and len(name_full.split()) == 1:
        queries.append(f'"{name_full}" 캐릭터 이름')
    return queries


def is_bot_detected(content, url):
    lowered = content.lower()
    if "unusual traffic" in lowered or "captcha" in lowered:
        return True
    if "sorry" in lowered and "google" in lowered:
        return True
    if "우리 시스템에서 비정상적인 트래픽" in content:
        return True
    if "자동화된" in content and "트래픽" in content:
        return True
    if "sorry" in (url or "") and "/sorry" in (url or ""):
        return True
    return False


async def search_google_with_retry(page, name_full, name_native, rate_limiter, cooldown, max_retries=2):
    """구글 검색 (재시도 포함)"""
    queries = build_queries(name_full, name_native)

    for query in queries:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko&gl=kr"
        for attempt in range(max_retries):
            try:
                await cooldown.wait()
                await rate_limiter.wait()

                await page.goto(
                    search_url,
                    timeout=PAGE_TIMEOUT,
                    wait_until='domcontentloaded'
                )

                content = await page.content()
                if is_bot_detected(content, page.url):
                    log_error(f"Bot detection for {name_full}, attempt {attempt + 1}")
                    await cooldown.trigger(30 + random.uniform(5, 15))  # 쿨다운 감소
                    await asyncio.sleep(2)  # 대기 시간 감소
                    continue

                page_text = await page.evaluate("document.body.innerText")  # 즉시 실행
                korean_name, reason = extract_korean_name_from_google(page_text, name_full, name_native)
                if korean_name:
                    return korean_name, reason

            except PlaywrightTimeout:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # 대기 시간 감소
                    continue
                log_error(f"Timeout for {name_full}")
                return None, None
            except Exception as e:
                log_error(f"Error for {name_full}: {e}")
                return None, None

    return None, None


async def create_browser(playwright, worker_id):
    """브라우저 생성 헬퍼 함수 (봇 감지 우회 강화)"""
    user_agent = random.choice(USER_AGENTS)
    browser = await playwright.chromium.launch(
        headless=False,  # 실제 브라우저 사용으로 봇 감지 우회
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]
    )
    context = await browser.new_context(
        user_agent=user_agent,
        locale='ko-KR',
        viewport={'width': 1280, 'height': 720},  # 작은 뷰포트
        java_script_enabled=True,
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)

    # 이미지, CSS, 폰트 차단으로 속도 향상
    await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
    await context.route("**/*.{woff,woff2,ttf,otf,eot}", lambda route: route.abort())
    await context.route("**/fonts.googleapis.com/**", lambda route: route.abort())
    await context.route("**/fonts.gstatic.com/**", lambda route: route.abort())

    page = await context.new_page()
    return browser, context, page


async def close_browser_safely(browser, context, page):
    """브라우저 안전하게 닫기"""
    try:
        if page:
            await page.close()
    except:
        pass
    try:
        if context:
            await context.close()
    except:
        pass
    try:
        if browser:
            await browser.close()
    except:
        pass


async def worker(worker_id, queue, result_queue, playwright, rate_limiter, cooldown):
    """Worker - 구글 검색 수행 (크래시 방지 강화)"""

    browser = None
    context = None
    page = None
    consecutive_failures = 0
    max_consecutive_failures = 5
    max_browser_restarts = 10
    browser_restarts = 0

    try:
        browser, context, page = await create_browser(playwright, worker_id)
        log(f"Worker {worker_id}: 시작")

        while True:
            # 큐에서 캐릭터 가져오기
            try:
                character = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            if stop_requested:
                await queue.put(character)
                break

            char_id = character['id']
            name_full = character['name_full']
            name_native = character['name_native']
            current_korean = character['name_korean']

            # 개별 캐릭터 처리를 try-except로 감싸기
            try:
                found_korean, reason = await search_google_with_retry(
                    page, name_full, name_native, rate_limiter, cooldown
                )

                if found_korean:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                await result_queue.put({
                    "id": char_id,
                    "name_full": name_full,
                    "name_native": name_native,
                    "current_korean": current_korean,
                    "found_korean": found_korean,
                    "reason": reason
                })

            except Exception as e:
                # 개별 처리 실패 시 에러 로그 후 계속 진행
                log_error(f"Worker {worker_id} error processing {name_full}: {e}")
                consecutive_failures += 1

                # 결과는 실패로 기록
                await result_queue.put({
                    "id": char_id,
                    "name_full": name_full,
                    "name_native": name_native,
                    "current_korean": current_korean,
                    "found_korean": None,
                    "reason": "error"
                })

            # 연속 실패 시 브라우저 재시작
            if consecutive_failures >= max_consecutive_failures:
                if browser_restarts >= max_browser_restarts:
                    log(f"Worker {worker_id}: 최대 재시작 횟수 초과, 종료")
                    break

                log(f"Worker {worker_id}: 연속 실패 {consecutive_failures}회, 브라우저 재시작 ({browser_restarts + 1}/{max_browser_restarts})...")
                await close_browser_safely(browser, context, page)
                await asyncio.sleep(3 + random.uniform(0, 2))  # 대기 시간 감소

                try:
                    browser, context, page = await create_browser(playwright, worker_id)
                    consecutive_failures = 0
                    browser_restarts += 1
                except Exception as e:
                    log_error(f"Worker {worker_id} browser restart failed: {e}")
                    await asyncio.sleep(5)  # 대기 시간 감소
                    try:
                        browser, context, page = await create_browser(playwright, worker_id)
                        consecutive_failures = 0
                        browser_restarts += 1
                    except:
                        log(f"Worker {worker_id}: 브라우저 재시작 실패, 종료")
                        break

            # 랜덤 딜레이 (봇 감지 우회)
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

    except Exception as e:
        log_error(f"Worker {worker_id} fatal error: {e}")

    finally:
        await close_browser_safely(browser, context, page)
        log(f"Worker {worker_id}: 종료")


async def writer(result_queue, total_count, progress):
    """단일 writer - DB 업데이트 및 진행상황 기록"""
    global _global_progress
    _global_progress = progress  # 전역 참조 설정 (긴급 저장용)

    processed_count = 0
    success_count = 0
    updated_count = 0
    last_save_time = time.time()

    processed_ids = set(progress.get("processed_ids", []))
    same_ids = set(progress.get("same", []))
    not_found_ids = set(progress.get("not_found", []))
    updated_map = progress.get("updated", {})
    errors = progress.get("errors", [])

    conn = sqlite3.connect(str(DATABASE_PATH), timeout=60.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    cursor = conn.cursor()

    try:
        while processed_count < total_count:
            result = await result_queue.get()
            if result is None:
                break

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

            processed_ids.add(char_id)

            if processed_count % SAVE_EVERY == 0 or (time.time() - last_save_time) >= SAVE_INTERVAL:
                conn.commit()
                progress["processed_ids"] = list(processed_ids)
                progress["same"] = list(same_ids)
                progress["not_found"] = list(not_found_ids)
                progress["updated"] = updated_map
                progress["errors"] = errors
                save_progress(progress)
                last_save_time = time.time()

            if processed_count % 10 == 0:
                rate = success_count / processed_count * 100 if processed_count > 0 else 0
                log(f"\n{'='*50}")
                log(f"📊 진행: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%)")
                log(f"   찾음: {success_count}개 ({rate:.1f}%)")
                log(f"   업데이트: {updated_count}개")
                log(f"{'='*50}\n")

        conn.commit()
    finally:
        conn.close()

    progress["processed_ids"] = list(processed_ids)
    progress["same"] = list(same_ids)
    progress["not_found"] = list(not_found_ids)
    progress["updated"] = updated_map
    progress["errors"] = errors
    save_progress(progress)

    return processed_count, success_count, updated_count


def emergency_save():
    """긴급 저장 - 프로그램 종료 시 호출"""
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
    log(f"⚠ 종료 신호 수신 (signal={signum}). 현재 처리 중인 항목까지 저장 후 종료합니다.")
    emergency_save()


# atexit 핸들러 등록
atexit.register(emergency_save)


async def main():
    global MIN_DELAY, MAX_DELAY, MAX_WORKERS, MAX_CHARACTERS, GLOBAL_MIN_INTERVAL, MIN_SCORE

    parser = argparse.ArgumentParser(description="구글 검색으로 캐릭터 한국어 이름 검증/업데이트")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--min-delay", type=float, default=MIN_DELAY)
    parser.add_argument("--max-delay", type=float, default=MAX_DELAY)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-interval", type=float, default=GLOBAL_MIN_INTERVAL)
    parser.add_argument("--min-score", type=int, default=MIN_SCORE)
    args = parser.parse_args()

    MAX_WORKERS = max(1, args.workers)
    MIN_DELAY = max(0.5, args.min_delay)
    MAX_DELAY = max(MIN_DELAY, args.max_delay)
    MAX_CHARACTERS = args.limit
    GLOBAL_MIN_INTERVAL = max(0.2, args.min_interval)
    MIN_SCORE = max(1, args.min_score)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log("=" * 60)
    log("🔍 구글 검색으로 모든 캐릭터 한국어 이름 업데이트")
    log(f"   Worker: {MAX_WORKERS}개")
    log(f"   딜레이: {MIN_DELAY}~{MAX_DELAY}초 (랜덤)")
    log(f"   글로벌 간격: {GLOBAL_MIN_INTERVAL}초")
    log(f"   최소 점수: {MIN_SCORE}")
    log("=" * 60)

    progress = load_progress()
    processed_ids = progress.get("processed_ids", [])

    if processed_ids:
        log(f"\n📂 이전 진행 상황:")
        log(f"   처리됨: {len(processed_ids)}개")
        log(f"   업데이트: {len(progress.get('updated', {}))}개")
        log(f"   동일: {len(progress.get('same', []))}개")
        log(f"   못찾음: {len(progress.get('not_found', []))}개")

    log("\n📋 캐릭터 조회 중...")
    characters = get_all_characters(limit=MAX_CHARACTERS, exclude_ids=processed_ids)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    queue = asyncio.Queue()
    for char in characters:
        await queue.put(char)

    result_queue = asyncio.Queue()

    log(f"\n🔄 검색 시작...")
    log(f"   예상 시간: {total_count * (MIN_DELAY + MAX_DELAY) / 2 / MAX_WORKERS / 60:.0f}분")
    start_time = datetime.now()

    async with async_playwright() as p:
        rate_limiter = GlobalRateLimiter(GLOBAL_MIN_INTERVAL)
        cooldown = GlobalCooldown()

        writer_task = asyncio.create_task(writer(result_queue, total_count, progress))
        workers_tasks = [
            worker(i, queue, result_queue, p, rate_limiter, cooldown)
            for i in range(MAX_WORKERS)
        ]
        await asyncio.gather(*workers_tasks)
        await result_queue.put(None)
        processed_count, success_count, updated_count = await writer_task

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
    asyncio.run(main())
