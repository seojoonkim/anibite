#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 크롤러 v4
정밀 매칭: 문서 상단에서 일본어 원문이 정확히 일치하는지 확인
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
MAX_CHARACTERS = 20  # None = 전체
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


def is_valid_korean_name(text):
    """한글 캐릭터 이름으로 유효한지"""
    if not text:
        return False

    text = text.strip()

    # 순수 한글 + 공백만
    if not re.match(r'^[가-힣]+(\s[가-힣]+)?$', text):
        return False

    # 길이 체크 (2-10자)
    clean = text.replace(' ', '')
    if len(clean) < 2 or len(clean) > 10:
        return False

    # 비이름 단어 필터
    blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                 '편집', '토론', '역사', '최근', '수정', '시각', '기능',
                 '작품', '시리즈', '애니', '만화', '게임', '소설']

    if text in blacklist or any(b in text for b in blacklist):
        return False

    return True


def check_name_match_in_header(page_text, name_native):
    """
    문서 상단(첫 100줄)에서 일본어 이름이 캐릭터 프로필에 있는지 확인
    단순히 페이지 어딘가에 언급된 것이 아닌, 캐릭터 정보로서 있는지 확인
    """
    lines = page_text.split('\n')[:100]
    header_text = '\n'.join(lines)

    # 한자만 추출 (히라가나/가타카나 제거)
    native_kanji = re.sub(r'[\u3040-\u309f\u30a0-\u30ff\s]', '', name_native)

    # 패턴 1: 일본어|영어 형식 (캐릭터 인포박스의 전형적 패턴)
    # 예: 金木研｜Ken Kaneki 또는 夜神月｜Light Yagami
    pattern1 = re.escape(name_native) + r'[|｜]'
    if re.search(pattern1, header_text):
        return True

    # 패턴 2: 한자만 있는 경우 한자|영어
    if len(native_kanji) >= 2:
        pattern2 = re.escape(native_kanji) + r'[|｜]'
        if re.search(pattern2, header_text):
            return True

    # 패턴 3: 후리가나가 섞인 형태 (金カネ木キ研ケン 같은)
    # 한자 각 글자 사이에 히라가나가 들어간 패턴
    if len(native_kanji) >= 2:
        # 한자들 사이에 히라가나가 있는 패턴 생성
        furigana_pattern = ''
        for char in native_kanji:
            furigana_pattern += re.escape(char) + r'[\u3040-\u309f\u30a0-\u30ff]*'
        furigana_pattern += r'[|｜]'

        if re.search(furigana_pattern, header_text):
            return True

    # 패턴 4: 테이블에서 "일본어 이름" 같은 레이블 근처
    # "이름" 레이블 전후 5줄 내에 일본어 이름이 있는지
    for i, line in enumerate(lines):
        if '이름' in line or '본명' in line or '성명' in line:
            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+5)])
            if name_native in context:
                return True
            if len(native_kanji) >= 2 and native_kanji in context:
                return True

    return False


def extract_korean_name_from_header(page_text):
    """문서 상단에서 한글 제목/이름 추출"""
    lines = page_text.split('\n')

    for line in lines[:15]:
        line = line.strip()
        if is_valid_korean_name(line):
            return line

    return None


async def find_korean_name(page, name_native, name_full):
    """나무위키에서 한국어 이름 찾기"""

    # 방법 1: 일본어 이름으로 직접 검색
    search_url = f"https://namu.wiki/Search?q={quote(name_native)}"

    try:
        await page.goto(search_url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)

        current_url = page.url

        # 검색 결과에서 한글 캐릭터명 후보 추출
        results = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();

                document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                    const text = a.innerText.trim();
                    const href = a.getAttribute('href');

                    // URL 디코딩해서 한글 확인
                    if (href.includes('#') || href.includes(':')) return;
                    if (seen.has(href)) return;
                    seen.add(href);

                    items.push({text: text, href: href});
                });

                return items.slice(0, 30);
            }
        """)

        # 한글 캐릭터 이름 패턴인 결과만 필터링
        korean_candidates = []
        for r in results:
            text = r['text']
            href = r['href']

            # URL에서 한글 이름 추출
            try:
                decoded = unquote(href.replace('/w/', ''))
                # 괄호 제거 (작품명 등)
                decoded = re.sub(r'\([^)]*\)$', '', decoded).strip()

                if is_valid_korean_name(decoded):
                    korean_candidates.append({'name': decoded, 'href': href})
            except:
                pass

            # 텍스트에서도 확인
            if is_valid_korean_name(text):
                korean_candidates.append({'name': text, 'href': href})

        # 중복 제거
        seen_names = set()
        unique_candidates = []
        for c in korean_candidates:
            if c['name'] not in seen_names:
                seen_names.add(c['name'])
                unique_candidates.append(c)

        # 각 후보 문서에서 일본어 이름 확인
        for candidate in unique_candidates[:10]:
            korean_name = candidate['name']
            href = candidate['href']

            try:
                doc_url = f"https://namu.wiki{href}"
                await page.goto(doc_url, timeout=10000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(0.3)

                page_text = await page.evaluate("document.body.innerText")

                # 문서가 없는 경우 스킵
                if "해당 문서를 찾을 수 없습니다" in page_text:
                    continue

                # 문서 상단에서 정확한 일본어 이름 매칭 확인
                if check_name_match_in_header(page_text, name_native):
                    # 문서 제목에서 한글 이름 확인
                    title_korean = extract_korean_name_from_header(page_text)
                    if title_korean:
                        return title_korean
                    return korean_name

            except Exception:
                pass

            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        pass

    return None


async def worker(worker_id, queue, context, total_count):
    """Worker that processes characters from queue"""
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
            except Exception:
                pass

            # 카운터 업데이트
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
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v4")
    log(f"   정밀 매칭 + {MAX_WORKERS}개 병렬 Worker")
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
