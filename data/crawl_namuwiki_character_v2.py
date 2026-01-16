#!/usr/bin/env python3
"""
나무위키 캐릭터 한국어 이름 병렬 크롤러 v2
Playwright 사용 (CSR 대응)
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
MAX_WORKERS = 5  # 5개 병렬
MAX_CHARACTERS = None  # None = 전체
REQUEST_DELAY = 1.0  # 요청 간격


# Global counters
processed_count = 0
success_count = 0
lock = asyncio.Lock()


def log(msg):
    """Immediate flush logging"""
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
        ORDER BY c.favourites DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    return db.execute_query(query)


def build_search_urls(name_native, name_full):
    """검색할 URL 목록 생성"""
    urls = []

    # 1. 일본어 이름으로 검색 (최우선)
    if name_native:
        urls.append(f"https://namu.wiki/w/{quote(name_native)}")

    # 2. 영어 이름 (Last First 형식 시도)
    if name_full:
        parts = name_full.split()
        if len(parts) >= 2:
            # "Lelouch Lamperouge" -> "Lamperouge Lelouch" 시도하지 않음
            # 대신 그대로 시도
            urls.append(f"https://namu.wiki/w/{quote(name_full)}")

    return urls


def extract_korean_name_from_text(text, name_native, name_full):
    """페이지 텍스트에서 한국어 이름 추출"""
    lines = text.split('\n')

    # 검색 패턴들
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 패턴 1: 한글이름만 있는 줄 (캐릭터 이름 특징: 2-6글자, 공백 포함 가능)
        # 보통 문서 상단에 한글 이름이 먼저 나옴
        if re.match(r'^[가-힣]+(\s[가-힣]+)?$', line) and 2 <= len(line.replace(' ', '')) <= 10:
            # 다음 줄에 일본어나 영어 이름이 있는지 확인
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 일본어 이름이 포함되어 있으면 이 한글이름이 맞음
                if name_native and name_native in next_line:
                    return line
                # 영어 이름이 포함되어 있으면
                if name_full and name_full.lower() in next_line.lower():
                    return line

        # 패턴 2: "한글이름 (일본어, English)" 형식
        match = re.match(r'^([가-힣]+(?:\s[가-힣]+)?)\s*[\(（]', line)
        if match:
            korean = match.group(1).strip()
            if len(korean) >= 2 and len(korean) <= 10:
                # 괄호 안에 일본어나 영어가 있는지 확인
                if name_native and name_native in line:
                    return korean
                if name_full and name_full.lower() in line.lower():
                    return korean

        # 패턴 3: 테이블에서 "이름" 레이블 다음에 나오는 한글
        if '이름' in line or '본명' in line or '성명' in line:
            # 같은 줄이나 다음 줄에서 한글 이름 찾기
            korean_matches = re.findall(r'[가-힣]{2,6}(?:\s[가-힣]{1,4})?', line)
            for km in korean_matches:
                if km not in ['이름', '본명', '성명', '등장인물', '주인공', '캐릭터']:
                    return km

            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                korean_matches = re.findall(r'[가-힣]{2,6}(?:\s[가-힣]{1,4})?', next_line)
                for km in korean_matches:
                    if km not in ['이름', '본명', '성명', '등장인물', '주인공', '캐릭터']:
                        return km

    # 패턴 4: 첫 번째 한글 이름 (문서 제목이 한글인 경우)
    first_korean = re.search(r'^([가-힣]{2,6}(?:\s[가-힣]{1,4})?)', text)
    if first_korean:
        name = first_korean.group(1)
        blacklist = ['목차', '개요', '등장인물', '주인공', '캐릭터', '설명', '특징']
        if name not in blacklist:
            return name

    return None


async def crawl_single_character(context, character, total_count, semaphore):
    """단일 캐릭터 크롤링"""
    global processed_count, success_count

    char_id = character['id']
    name_full = character['name_full']
    name_native = character['name_native']

    korean_name = None

    async with semaphore:
        page = await context.new_page()

        try:
            urls = build_search_urls(name_native, name_full)

            for url in urls:
                try:
                    await page.goto(url, timeout=15000)
                    await page.wait_for_load_state('domcontentloaded')
                    await asyncio.sleep(0.3)

                    # 페이지 텍스트 추출
                    text = await page.evaluate("document.body.innerText")

                    # 페이지가 없는 경우
                    if "해당 문서를 찾을 수 없습니다" in text:
                        continue

                    # 한글 이름 추출
                    korean_name = extract_korean_name_from_text(text, name_native, name_full)

                    if korean_name:
                        # DB 업데이트
                        db.execute_update(
                            "UPDATE character SET name_korean = ? WHERE id = ?",
                            (korean_name, char_id)
                        )
                        break

                except Exception as e:
                    pass

                await asyncio.sleep(REQUEST_DELAY)

        finally:
            await page.close()

    # 카운터 업데이트 (thread-safe)
    async with lock:
        processed_count += 1
        current = processed_count

        if korean_name:
            success_count += 1
            log(f"✓ [{current}/{total_count}] {name_full} → {korean_name}")
        else:
            log(f"✗ [{current}/{total_count}] {name_full}")

        # 10개마다 진행상황
        if current % 10 == 0:
            rate = success_count / current * 100 if current > 0 else 0
            log(f"\n{'='*60}")
            log(f"📊 진행상황: {current}/{total_count} ({current/total_count*100:.1f}%)")
            log(f"   성공: {success_count}개 ({rate:.1f}%)")
            log(f"   실패: {current - success_count}개")
            log(f"{'='*60}\n")

    return korean_name


async def main():
    global processed_count, success_count

    log("=" * 60)
    log("🚀 나무위키 캐릭터 한국어 이름 크롤러 v2")
    log(f"   Playwright 사용, {MAX_WORKERS}개 병렬 처리")
    log("=" * 60)

    # 캐릭터 조회
    log("\n📋 처리할 캐릭터 조회 중...")
    characters = get_characters_to_crawl(limit=MAX_CHARACTERS)
    total_count = len(characters)

    log(f"   총 {total_count}개 캐릭터 발견")

    if total_count == 0:
        log("✅ 처리할 캐릭터가 없습니다!")
        return

    # 카운터 초기화
    processed_count = 0
    success_count = 0

    log(f"\n🔄 크롤링 시작...")
    start_time = datetime.now()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        # 세마포어로 동시 실행 제한
        semaphore = asyncio.Semaphore(MAX_WORKERS)

        # 모든 작업 생성
        tasks = [
            crawl_single_character(context, char, total_count, semaphore)
            for char in characters
        ]

        # 병렬 실행
        await asyncio.gather(*tasks)

        await context.close()
        await browser.close()

    # 최종 결과
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
