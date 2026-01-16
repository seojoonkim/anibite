#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 병렬 크롤러 v3
검색 기능 사용 + 일본어 이름 매칭
5개 병렬 처리, 10개마다 진행상황 알림
"""
import sys
import os
import re
import asyncio
from urllib.parse import quote
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# Configuration
MAX_WORKERS = 5
MAX_CHARACTERS = 30  # None = 전체, 테스트용 30
REQUEST_DELAY = 0.8


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


def normalize_japanese(text):
    """일본어 이름 정규화 (공백, 후리가나 제거)"""
    if not text:
        return ""
    # 히라가나/가타카나 공백 제거
    text = re.sub(r'\s+', '', text)
    return text


def extract_japanese_from_page(text):
    """페이지에서 일본어 이름 추출 (히라가나 제거된 한자 버전)"""
    names = []

    # 패턴: 한자(후리가나)한자(후리가나) | English
    # 예: 金カネ木キ 研ケン｜Ken Kaneki
    pattern = r'([\u4e00-\u9fff][\u3040-\u309f\u30a0-\u30ff]?)+[|｜]'
    matches = re.findall(pattern, text)

    # 순수 한자만 추출
    for line in text.split('\n')[:50]:  # 상위 50줄만
        # 한자가 포함된 줄에서 한자만 추출
        kanji_only = re.sub(r'[\u3040-\u309f\u30a0-\u30ff\s]', '', line)  # 히라가나/가타카나 제거
        if re.match(r'^[\u4e00-\u9fff]{2,}$', kanji_only):
            names.append(kanji_only)

    return names


def match_japanese_name(page_text, target_native):
    """페이지 텍스트에서 타겟 일본어 이름 매칭 확인"""
    target_normalized = normalize_japanese(target_native)

    # 정확히 일치
    if target_native in page_text or target_normalized in page_text:
        return True

    # 한자만 비교 (히라가나/가타카나 제거)
    target_kanji = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]', '', target_native)
    if len(target_kanji) >= 2:
        # 페이지에서 한자 추출
        page_kanji_matches = extract_japanese_from_page(page_text)
        if target_kanji in page_kanji_matches:
            return True
        # 페이지 전체에서 한자 검색
        if target_kanji in page_text:
            return True

    return False


def extract_korean_name_from_title(text):
    """문서 첫 부분에서 한글 이름 추출"""
    lines = text.split('\n')

    for line in lines[:20]:  # 상위 20줄
        line = line.strip()
        if not line:
            continue

        # 순수 한글 이름 (2-10자, 공백 포함 가능)
        if re.match(r'^[가-힣]+(\s[가-힣]+)?$', line):
            name = line.strip()
            # 흔한 비-이름 단어 필터
            blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '특징', '분류',
                        '편집', '토론', '역사', '최근', '수정', '시각', '기능']
            if name not in blacklist and 2 <= len(name.replace(' ', '')) <= 10:
                return name

    return None


async def search_and_match(page, name_native, name_full):
    """나무위키 검색 후 일본어 이름 매칭으로 한글 이름 찾기"""
    search_url = f"https://namu.wiki/Search?q={quote(name_native)}"

    try:
        await page.goto(search_url, timeout=15000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(0.5)

        current_url = page.url

        # 문서로 직접 리다이렉트된 경우
        if "/Search" not in current_url and "/w/" in current_url:
            text = await page.evaluate("document.body.innerText")
            if match_japanese_name(text, name_native):
                korean = extract_korean_name_from_title(text)
                if korean:
                    return korean

        # 검색 결과 페이지인 경우
        links = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('a[href^="/w/"]').forEach(a => {
                    const text = a.innerText.trim();
                    // 한글 이름 패턴 (2-15자)
                    if (/^[가-힣]+(?:\\s[가-힣]+)?$/.test(text) && text.length >= 2 && text.length <= 15) {
                        results.push({href: a.getAttribute('href'), text: text});
                    }
                });
                // 중복 제거
                const seen = new Set();
                return results.filter(r => {
                    if (seen.has(r.text)) return false;
                    seen.add(r.text);
                    return true;
                }).slice(0, 10);
            }
        """)

        # 검색 결과 중 일본어 이름이 매칭되는 문서 찾기
        for link in links:
            korean_candidate = link['text']
            href = link['href']

            # 비-이름 필터
            blacklist = ['목차', '개요', '등장인물', '주인공', '설명', '분류']
            if korean_candidate in blacklist:
                continue

            # 해당 문서 방문하여 일본어 이름 확인
            doc_url = f"https://namu.wiki{href}"

            try:
                await page.goto(doc_url, timeout=10000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(0.3)

                doc_text = await page.evaluate("document.body.innerText")

                if match_japanese_name(doc_text, name_native):
                    return korean_candidate

            except:
                continue

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
                korean_name = await search_and_match(page, name_native, name_full)

                if korean_name:
                    db.execute_update(
                        "UPDATE character SET name_korean = ? WHERE id = ?",
                        (korean_name, char_id)
                    )
            except Exception as e:
                pass

            # 카운터 업데이트
            async with lock:
                processed_count += 1
                current = processed_count

                if korean_name:
                    success_count += 1
                    log(f"✓ [{current}/{total_count}] {name_full} ({name_native}) → {korean_name}")
                else:
                    log(f"✗ [{current}/{total_count}] {name_full} ({name_native})")

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
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v3")
    log(f"   검색+매칭 방식, {MAX_WORKERS}개 병렬 Worker")
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

    # 작업 큐 생성
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

        # Worker들 병렬 실행
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
    log(f"  성공: {success_count}개 ({success_count/processed_count*100:.1f}%)")
    log(f"  실패: {processed_count - success_count}개")
    log(f"  소요 시간: {elapsed/60:.1f}분")
    log(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
