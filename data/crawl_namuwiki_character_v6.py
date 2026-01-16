#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v6
개선된 검증: 캐릭터 문서인지 확인 (성우/출생/등장인물 정보 존재 여부)
5개 병렬 Worker, 10개마다 진행상황
"""
import sys
import os
import re
import asyncio
from urllib.parse import quote, unquote
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed")
    sys.exit(1)


# Configuration
MAX_WORKERS = 5
MAX_CHARACTERS = 30  # None = 전체
REQUEST_DELAY = 0.5


# Global counters
processed_count = 0
success_count = 0
lock = asyncio.Lock()


def log(msg):
    print(msg, flush=True)


def get_characters_to_crawl(limit=None):
    """한국어 이름이 필요한 캐릭터 조회"""
    query = """
        SELECT DISTINCT
            c.id,
            c.name_full,
            c.name_native,
            c.favourites
        FROM character c
        WHERE c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra')
          AND c.name_native != ''
          AND LENGTH(c.name_native) >= 2
        ORDER BY c.favourites DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    return db.execute_query(query)


def extract_kanji(text):
    """문자열에서 한자만 추출"""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def is_valid_korean_name(text):
    """한글 캐릭터 이름으로 유효한지"""
    if not text:
        return False

    text = text.strip()

    if not re.match(r'^[가-힣]+(\s[가-힣]+)?$', text):
        return False

    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 10:
        return False

    blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '편집', '토론', '역사', '최근', '수정', '시각', '기능',
                 '작품', '시리즈', '애니', '만화', '게임', '소설', '더보기',
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주']

    if text in blacklist or any(b in text for b in blacklist):
        return False

    return True


def is_character_document(page_text):
    """
    페이지가 (애니메이션) 캐릭터 문서인지 확인

    캐릭터 문서 특징:
    - 성우 정보가 있음 (필수!)
    - 분류에 '등장인물'이 포함됨

    비캐릭터 문서 (거부):
    - 분류에 '배우', '성우', '가수' 등 실존 인물
    - '직업' 항목에 '배우', '성우'가 있음
    """
    header = page_text[:4000]  # 상단 4000자

    # === 비캐릭터 문서 필터링 ===

    # 1. 분류에서 실존 인물 확인 (분류는 보통 상단에 있음)
    category_line = ""
    for line in header.split('\n')[:15]:
        if '분류' in line:
            category_line = line
            break

    # 실존 인물 카테고리
    real_person_cats = ['남배우', '여배우', '성우', '가수', '아이돌',
                        '출생', '데뷔', '출신 인물', '소속 연예인']
    for cat in real_person_cats:
        if cat in category_line:
            return False

    # 2. 직업란에 실존 인물 직업이 있으면 제외
    lines = header.split('\n')
    for i, line in enumerate(lines):
        if '직업' in line:
            context = '\n'.join(lines[max(0, i-1):min(len(lines), i+3)])
            if '배우' in context or '아역' in context:
                return False

    # === 캐릭터 문서 확인 ===

    # 1. 성우 정보 (필수)
    if '성우' not in header:
        return False

    # 2. 분류에 등장인물 포함 (보너스)
    has_character_cat = '등장인물' in category_line or '/등장인물' in header

    # 3. 캐릭터 프로필 정보
    profile_count = 0
    char_keywords = ['종족', 'Rc 타입', '능력', '쿼크', '혈액형', '1인칭']
    for kw in char_keywords:
        if kw in header:
            profile_count += 1

    # 성우 정보가 있고, (등장인물 분류 OR 캐릭터 프로필이 있으면) 캐릭터 문서
    return has_character_cat or profile_count >= 1


def find_japanese_name_match(page_text, target_native):
    """
    페이지에서 일본어 이름 매칭 확인
    """
    target_kanji = extract_kanji(target_native)

    # 패턴 1: 직접 일치
    if target_native in page_text:
        return True

    # 패턴 2: 한자만 비교 (2자 이상인 경우만)
    if len(target_kanji) >= 2:
        # 상단 2000자에서 찾기
        header = page_text[:2000]

        # 후리가나가 섞인 형태에서 한자 추출 후 비교
        # 예: 金カネ木キ研ケン -> 金木研
        lines = header.split('\n')
        for line in lines:
            if '/' in line or '｜' in line or '|' in line:
                line_kanji = extract_kanji(line)
                if target_kanji == line_kanji:
                    return True

        # 한자가 연속으로 있는 경우
        if target_kanji in header:
            return True

    return False


def extract_korean_title(page_text):
    """페이지 상단에서 한글 제목 추출"""
    lines = page_text.split('\n')

    for line in lines[:20]:
        line = line.strip()
        if is_valid_korean_name(line):
            return line

    return None


async def find_korean_name(page, name_native, name_full):
    """나무위키에서 한국어 이름 찾기"""
    search_url = f"https://namu.wiki/Search?q={quote(name_native)}"

    try:
        await page.goto(search_url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)

        # 검색 결과에서 URL 추출
        results = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();

                document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href.includes('#') || href.includes(':')) return;
                    if (seen.has(href)) return;
                    seen.add(href);
                    items.push(href);
                });

                return items.slice(0, 30);
            }
        """)

        # 한글 이름 URL만 필터링
        korean_candidates = []
        for href in results:
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
        for candidate in unique[:10]:
            korean_name = candidate['name']
            href = candidate['href']

            try:
                doc_url = f"https://namu.wiki{href}"
                await page.goto(doc_url, timeout=10000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(0.3)

                page_text = await page.evaluate("document.body.innerText")

                if "해당 문서를 찾을 수 없습니다" in page_text:
                    continue

                # 1. 캐릭터 문서인지 확인
                if not is_character_document(page_text):
                    continue

                # 2. 일본어 이름 매칭 확인
                if find_japanese_name_match(page_text, name_native):
                    title = extract_korean_title(page_text)
                    if title:
                        return title
                    return korean_name

            except:
                pass

            await asyncio.sleep(REQUEST_DELAY)

    except:
        pass

    return None


async def worker(worker_id, queue, context, total_count):
    """Worker"""
    global processed_count, success_count

    page = await context.new_page()

    try:
        while True:
            try:
                character = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            char_id = character['id']
            name_full = character['name_full']
            name_native = character['name_native']

            korean_name = None

            try:
                korean_name = await find_korean_name(page, name_native, name_full)

                if korean_name:
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (korean_name, char_id)
                    )
            except:
                pass

            async with lock:
                processed_count += 1
                current = processed_count

                if korean_name:
                    success_count += 1
                    log(f"✓ [{current}/{total_count}] {name_full} ({name_native}) → {korean_name}")
                else:
                    log(f"✗ [{current}/{total_count}] {name_full}")

                if current % 10 == 0:
                    rate = success_count / current * 100 if current > 0 else 0
                    log(f"\n{'='*60}")
                    log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
                    log(f"   성공: {success_count}개 ({rate:.1f}%)")
                    log(f"   실패: {current - success_count}개")
                    log(f"{'='*60}\n")

    finally:
        await page.close()


async def main():
    global processed_count, success_count

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v6")
    log(f"   캐릭터 문서 검증 + {MAX_WORKERS}개 병렬 Worker")
    log("=" * 60)

    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 발견")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    processed_count = 0
    success_count = 0

    queue = asyncio.Queue()
    for char in characters:
        await queue.put(char)

    log(f"\n🔄 크롤링 시작 ({MAX_WORKERS}개 Worker)...")
    start_time = datetime.now()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        workers = [
            worker(i, queue, context, total_count)
            for i in range(MAX_WORKERS)
        ]

        await asyncio.gather(*workers)

        await context.close()
        await browser.close()

    elapsed = (datetime.now() - start_time).total_seconds()

    log(f"\n\n{'='*60}")
    log("🎉 크롤링 완료!")
    log(f"{'='*60}")
    log(f"  총 처리: {processed_count}개")
    if processed_count > 0:
        log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
        log(f"  실패: {processed_count - success_count}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
