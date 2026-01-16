#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v5
정확한 한자 매칭: 후리가나가 섞인 형태에서 한자 추출 후 비교
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
                 '작품', '시리즈', '애니', '만화', '게임', '소설', '더보기']

    if text in blacklist or any(b in text for b in blacklist):
        return False

    return True


def find_japanese_name_in_page(page_text, target_native):
    """
    페이지에서 일본어 이름 확인
    나무위키 형식: 夜や神がみ 月ライト / Light Yagami
    """
    target_kanji = extract_kanji(target_native)

    if len(target_kanji) < 2:
        # 한자가 2개 미만이면 원본 그대로 검색
        return target_native in page_text

    lines = page_text.split('\n')[:150]

    for line in lines:
        # 패턴 1: 한자+후리가나 / English 형식
        # 夜や神がみ 月ライト / Light Yagami
        if '/' in line or '｜' in line or '|' in line:
            # 슬래시나 파이프 앞부분에서 한자 추출
            parts = re.split(r'[/｜|]', line)
            if parts:
                japanese_part = parts[0]
                kanji_in_line = extract_kanji(japanese_part)

                # 한자가 일치하면 매칭
                if kanji_in_line and target_kanji == kanji_in_line:
                    return True

    # 패턴 2: 원본 일본어 이름이 그대로 있는 경우
    if target_native in page_text:
        return True

    # 패턴 3: 한자만 연속으로 있는 경우
    if target_kanji in page_text:
        # 단, 문서 상단 150줄 내에 있어야 함
        header = '\n'.join(lines)
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

        # 검색 결과에서 링크 추출
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

        # 한글 캐릭터 이름 패턴인 URL만 필터링
        korean_candidates = []
        for href in results:
            try:
                decoded = unquote(href.replace('/w/', ''))
                # 괄호 내용 제거
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

        # 각 후보 문서 확인
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

                # 일본어 이름 매칭 확인
                if find_japanese_name_in_page(page_text, name_native):
                    # 문서 제목에서 한글 이름 확인
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
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v5")
    log(f"   한자 매칭 + {MAX_WORKERS}개 병렬 Worker")
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
