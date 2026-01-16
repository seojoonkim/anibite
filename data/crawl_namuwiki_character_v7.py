#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v7
엄격한 매칭: 인포박스에서 일본어+영어 이름이 둘 다 일치해야 함
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
MAX_CHARACTERS = 50  # None = 전체, 테스트용
REQUEST_DELAY = 0.5


# Global counters
processed_count = 0
success_count = 0
lock = asyncio.Lock()


def log(msg):
    print(msg, flush=True)


def get_characters_to_crawl(limit=None):
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
    """한자만 추출"""
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def is_valid_korean_name(text):
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
                 '성우', '배우', '출생', '출신', '기타', '관계', '각주', '목록']
    if text in blacklist or any(b in text for b in blacklist):
        return False
    return True


def is_character_document(page_text):
    """캐릭터 문서인지 확인"""
    header = page_text[:4000]

    # 분류 확인
    category_line = ""
    for line in header.split('\n')[:15]:
        if '분류' in line:
            category_line = line
            break

    # 실존 인물 카테고리 제외
    real_person_cats = ['남배우', '여배우', '가수', '아이돌',
                        '출생', '데뷔', '출신 인물', '소속 연예인']
    for cat in real_person_cats:
        if cat in category_line:
            return False

    # 직업이 배우인 경우 제외 (캐릭터 설정상 배우는 OK)
    lines = header.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '직업':
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # "배우(xxxx년~)" 같은 패턴은 실존 인물
                if re.search(r'배우\s*\(\d{4}', next_line):
                    return False

    # 성우 정보 필수
    if '성우' not in header:
        return False

    return True


def match_infobox_name(page_text, target_native, target_english):
    """
    인포박스에서 일본어+영어 이름 엄격 매칭

    조건:
    1. 한자가 정확히 일치해야 함 (필수)
    2. 영어 이름이 일치하면 추가 검증 (선택)
    """
    target_kanji = extract_kanji(target_native)

    # 한자가 2자 미만이면 원본 그대로 사용
    if len(target_kanji) < 2:
        target_kanji = target_native

    # 영어 이름 (전체)
    english_full = target_english.lower().replace(' ', '')

    # 상단 80줄에서 인포박스 찾기
    lines = page_text.split('\n')[:80]

    for line in lines:
        # 일본어|영어 또는 일본어/영어 패턴
        if ('/' in line or '｜' in line or '|' in line) and re.search(r'[A-Za-z]', line):
            line_kanji = extract_kanji(line)

            # 한자 정확 일치 (필수!)
            if not line_kanji or target_kanji != line_kanji:
                continue

            # 한자가 정확히 일치하면, 영어도 확인
            line_english = ''.join(re.findall(r'[A-Za-z]+', line)).lower()

            # 영어가 충분히 일치하면 확실한 매칭
            if english_full and line_english:
                # 영어 이름이 70% 이상 일치하면 OK
                common = sum(1 for c in english_full if c in line_english)
                if common >= len(english_full) * 0.7:
                    return True

            # 한자만 정확히 일치해도 OK (영어가 없는 경우)
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


async def search_and_find(page, search_term, name_native, name_full):
    """검색 후 캐릭터 찾기"""
    search_url = f"https://namu.wiki/Search?q={quote(search_term)}"

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

        # 한글 이름 URL만
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
        for candidate in unique[:8]:
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

                # 1. 캐릭터 문서인지
                if not is_character_document(page_text):
                    continue

                # 2. 인포박스에서 일본어+영어 매칭
                if match_infobox_name(page_text, name_native, name_full):
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


async def find_korean_name(page, name_native, name_full):
    """나무위키에서 한국어 이름 찾기 (다중 검색)"""

    # 1. 일본어 이름으로 검색
    result = await search_and_find(page, name_native, name_native, name_full)
    if result:
        return result

    # 2. 영어 이름으로 검색
    result = await search_and_find(page, name_full, name_native, name_full)
    if result:
        return result

    # 3. 영어 이름 일부로 검색 (성만, 이름만)
    parts = name_full.split()
    if len(parts) >= 2:
        # 성으로 검색
        result = await search_and_find(page, parts[-1], name_native, name_full)
        if result:
            return result

    return None


async def worker(worker_id, queue, context, total_count):
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
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v7")
    log(f"   엄격한 매칭 + {MAX_WORKERS}개 병렬 Worker")
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
