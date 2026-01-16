#!/usr/bin/env python3
"""
구글 검색을 통해 캐릭터의 한국어 이름 찾기
구글 Knowledge Panel에서 "English Name (한국어 이름)" 패턴 추출
예: "Shinji Ikari (이카리 신지)"
"""
import sys
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db


def log(msg):
    print(msg, flush=True)


def search_korean_name(english_name):
    """구글 검색으로 한국어 이름 찾기 - Knowledge Panel 활용"""
    query = f"{english_name} 이름"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=ko"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        html = response.text

        # 패턴 1: Knowledge Panel - "English Name (한국어 이름)" 형태
        # 예: Shinji Ikari (이카리 신지)
        pattern1 = re.compile(
            re.escape(english_name.split()[0]) + r'[^(]*\(([가-힣]+\s*[가-힣]*)\)',
            re.IGNORECASE
        )
        match = pattern1.search(html)
        if match:
            korean_name = match.group(1).strip()
            if 2 <= len(korean_name.replace(' ', '')) <= 10:
                return korean_name

        # 패턴 2: 일반적인 괄호 안 한국어 이름
        # (한국어이름) 또는 (한국어 이름)
        pattern2 = r'\(([가-힣]{2,4}\s+[가-힣]{2,6})\)'
        matches = re.findall(pattern2, html)
        if matches:
            for korean_name in matches[:5]:
                # 필터링
                exclude_words = ['등장인물', '캐릭터', '애니메이션', '만화', '작품']
                if not any(w in korean_name for w in exclude_words):
                    return korean_name

        # 패턴 3: 붙어있는 한국어 이름
        pattern3 = r'\(([가-힣]{3,8})\)'
        matches = re.findall(pattern3, html)
        if matches:
            for korean_name in matches[:5]:
                exclude_words = ['등장인물', '캐릭터', '애니메이션', '만화', '작품', '시리즈', '주인공']
                if not any(w in korean_name for w in exclude_words):
                    if 3 <= len(korean_name) <= 8:
                        return korean_name

        return None

    except Exception as e:
        log(f"  Error searching {english_name}: {e}")
        return None


def search_top_characters(limit=100):
    """인기 캐릭터 상위 N개의 한국어 이름 검색"""

    log("=" * 80)
    log(f"구글 검색으로 인기 캐릭터 상위 {limit}개 한국어 이름 찾기")
    log("=" * 80)

    # 인기 캐릭터 가져오기
    characters = db.execute_query("""
        SELECT id, name_full, name_korean
        FROM character
        WHERE name_full IS NOT NULL AND name_full != ''
        ORDER BY favourites DESC
        LIMIT ?
    """, (limit,))

    log(f"\n{len(characters)}개 캐릭터 검색 시작...")

    results = {}
    success_count = 0

    for i, char in enumerate(characters):
        char_id = char['id']
        name_full = char['name_full']
        current_korean = char['name_korean']

        log(f"\n[{i+1}/{limit}] {name_full}")
        log(f"  현재: {current_korean}")

        # 구글 검색
        korean_name = search_korean_name(name_full)

        if korean_name:
            log(f"  검색 결과: {korean_name}")
            results[str(char_id)] = {
                'english': name_full,
                'current': current_korean,
                'searched': korean_name
            }
            success_count += 1
        else:
            log(f"  검색 실패")

        # 속도 제한 (구글 차단 방지)
        time.sleep(2)

    log(f"\n\n검색 완료: {success_count}/{limit}")

    # 결과 저장
    output_path = os.path.join(os.path.dirname(__file__), 'searched_korean_names.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log(f"저장: {output_path}")

    return results


def test_search():
    """몇 개 테스트"""
    test_names = [
        "Satoru Gojo",
        "Eren Yeager",
        "Naruto Uzumaki",
        "Light Yagami",
        "Levi Ackerman",
    ]

    log("테스트 검색:")
    for name in test_names:
        korean = search_korean_name(name)
        log(f"  {name} → {korean}")
        time.sleep(1)


if __name__ == "__main__":
    # 테스트
    test_search()

    # 본격 검색 (주의: 시간 오래 걸림, 구글 차단 가능)
    # search_top_characters(100)
