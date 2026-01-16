#!/usr/bin/env python3
"""
나무위키에서 인기 애니메이션 200개의 등장인물 한국어 이름 크롤링
"""
import sys
import os
import re
import json
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

def log(msg):
    print(msg, flush=True)

# 나무위키 등장인물 페이지 URL 패턴
NAMUWIKI_BASE = "https://namu.wiki/w/"

# 애니메이션 제목 → 나무위키 등장인물 페이지 매핑
ANIME_TO_NAMUWIKI = {
    # 인기 애니메이션들의 나무위키 등장인물 페이지
    "진격의 거인": "진격의 거인/등장인물",
    "원피스": "원피스(만화)/등장인물",
    "나루토": "나루토/등장인물",
    "나루토 질풍전": "나루토/등장인물",
    "블리치": "블리치(만화)/등장인물",
    "데스노트": "데스노트/등장인물",
    "강철의 연금술사": "강철의 연금술사/등장인물",
    "강철의 연금술사: 브라더후드": "강철의 연금술사/등장인물",
    "헌터X헌터": "헌터×헌터/등장인물",
    "주술회전": "주술회전/등장인물",
    "귀멸의 칼날": "귀멸의 칼날/등장인물",
    "체인소 맨": "체인소 맨/등장인물",
    "스파이 패밀리": "SPY×FAMILY/등장인물",
    "모브사이코 100": "모브 사이코 100/등장인물",
    "원펀맨": "원펀맨/등장인물",
    "나의 히어로 아카데미아": "나의 히어로 아카데미아/등장인물",
    "도쿄 구울": "도쿄 구울/등장인물",
    "소드 아트 온라인": "소드 아트 온라인/등장인물",
    "코드 기어스: 반역의 를루슈": "코드 기어스/등장인물",
    "신세기 에반게리온": "신세기 에반게리온/등장인물",
    "카우보이 비밥": "카우보이 비밥/등장인물",
    "스테인즈 게이트": "STEINS;GATE/등장인물",
    "Re: 제로부터 시작하는 이세계 생활": "Re:제로부터 시작하는 이세계 생활/등장인물",
    "빈란드 사가": "빈란드 사가/등장인물",
    "바이올렛 에버가든": "바이올렛 에버가든/등장인물",
    "장송의 프리렌": "장송의 프리렌/등장인물",
    "죠죠의 기묘한 모험": "죠죠의 기묘한 모험/등장인물",
    "블랙 클로버": "블랙 클로버/등장인물",
    "하이큐!!": "하이큐!!/등장인물",
    "무직전생": "무직전생/등장인물",
    "전생했더니 슬라임이었던 건에 대하여": "전생했더니 슬라임이었던 건에 대하여/등장인물",
    "이 멋진 세계에 축복을!": "이 멋진 세계에 축복을!/등장인물",
    "4월은 너의 거짓말": "4월은 너의 거짓말/등장인물",
    "목소리의 형태": "목소리의 형태",
    "너의 이름은": "너의 이름은./등장인물",
    "마법소녀 마도카☆마기카": "마법소녀 마도카☆마기카/등장인물",
    "메이드 인 어비스": "메이드 인 어비스/등장인물",
    "호리미야": "호리미야/등장인물",
    "청춘 돼지는 바니걸 선배의 꿈을 꾸지 않는다": "청춘 돼지 시리즈/등장인물",
    "카구야 님은 고백받고 싶어 ~천재들의 연애 두뇌전~": "카구야 님은 고백받고 싶어/등장인물",
    "봇치 더 록!": "봇치 더 록!/등장인물",
    "천원돌파 그렌라간": "천원돌파 그렌라간/등장인물",
    "사이버펑크: 엣지러너": "사이버펑크: 엣지러너/등장인물",
    "나만이 없는 거리": "나만이 없는 거리/등장인물",
    "닥터 스톤": "Dr. STONE/등장인물",
    "몬스터": "MONSTER/등장인물",
    "약사의 혼잣말": "약사의 혼잣말/등장인물",
}

def get_namuwiki_page(title):
    """나무위키 페이지 HTML 가져오기"""
    encoded_title = urllib.parse.quote(title)
    url = f"{NAMUWIKI_BASE}{encoded_title}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            log(f"Failed to fetch {url}: {response.status_code}")
            return None
    except Exception as e:
        log(f"Error fetching {url}: {e}")
        return None


def extract_character_names(html, anime_title):
    """HTML에서 캐릭터 이름 추출 (한국어 이름 + 영어/일본어 이름)"""
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    characters = []

    # 텍스트에서 캐릭터 이름 패턴 찾기
    # 일반적인 패턴: 한국어이름 (영어이름 / 일본어이름)
    text = soup.get_text()

    # 패턴 1: 한글이름 (영어이름)
    pattern1 = r'([가-힣]+(?:\s+[가-힣]+)?)\s*[\(（]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)\s*[\)）]'
    matches1 = re.findall(pattern1, text)

    # 패턴 2: 한글이름 (영어이름 / 일본어)
    pattern2 = r'([가-힣]+(?:\s+[가-힣]+)?)\s*[\(（]\s*([A-Za-z]+(?:\s+[A-Za-z\.]+)*)\s*[/／]\s*[ァ-ヶー・]+'
    matches2 = re.findall(pattern2, text)

    for korean, english in matches1 + matches2:
        korean = korean.strip()
        english = english.strip()

        # 필터링
        if len(korean) >= 2 and len(english) >= 2:
            # 일반적인 단어 제외
            if korean not in ['등장인물', '성우', '배우', '주인공', '조연', '기타', '애니', '만화']:
                characters.append({
                    'korean': korean,
                    'english': english,
                    'anime': anime_title
                })

    return characters


def match_with_db(characters):
    """DB의 캐릭터와 매칭"""
    matched = []

    for char in characters:
        english_name = char['english']
        korean_name = char['korean']

        # DB에서 영어 이름으로 검색
        results = db.execute_query("""
            SELECT id, name_full, name_native, name_korean
            FROM character
            WHERE LOWER(name_full) = LOWER(?)
               OR LOWER(name_full) LIKE LOWER(?)
            LIMIT 5
        """, (english_name, f"%{english_name}%"))

        if results:
            for r in results:
                # 이미 한국어 이름이 있으면 스킵 (나무위키가 더 정확할 수 있으니 덮어쓰기 옵션)
                matched.append({
                    'id': r['id'],
                    'name_full': r['name_full'],
                    'current_korean': r['name_korean'],
                    'new_korean': korean_name,
                    'source': 'namuwiki'
                })

    return matched


def crawl_top_anime():
    """인기 애니메이션 200개의 등장인물 크롤링"""

    log("=" * 80)
    log("나무위키 인기 애니메이션 등장인물 크롤링")
    log("=" * 80)

    # DB에서 인기 애니메이션 가져오기
    anime_list = db.execute_query("""
        SELECT id, title_romaji, title_korean
        FROM anime
        WHERE title_korean IS NOT NULL
        ORDER BY favourites DESC
        LIMIT 200
    """)

    log(f"인기 애니메이션 {len(anime_list)}개 로드")

    all_characters = []
    crawled_count = 0

    for anime in anime_list:
        anime_id = anime['id']
        title_korean = anime['title_korean']

        # 나무위키 페이지 매핑 확인
        namuwiki_page = ANIME_TO_NAMUWIKI.get(title_korean)

        if not namuwiki_page:
            # 기본 패턴 시도
            namuwiki_page = f"{title_korean}/등장인물"

        log(f"\n[{crawled_count + 1}] {title_korean} → {namuwiki_page}")

        # 나무위키 페이지 가져오기
        html = get_namuwiki_page(namuwiki_page)

        if html:
            characters = extract_character_names(html, title_korean)
            log(f"  → {len(characters)}명 발견")
            all_characters.extend(characters)
            crawled_count += 1
        else:
            # 등장인물 페이지가 없으면 메인 페이지 시도
            html = get_namuwiki_page(title_korean)
            if html:
                characters = extract_character_names(html, title_korean)
                log(f"  → (메인 페이지에서) {len(characters)}명 발견")
                all_characters.extend(characters)
                crawled_count += 1

        # 속도 제한
        time.sleep(0.5)

        # 테스트: 20개만
        if crawled_count >= 20:
            log("\n테스트 모드: 20개 애니메이션만 크롤링")
            break

    log(f"\n총 {len(all_characters)}명 캐릭터 발견")

    # DB 매칭
    matched = match_with_db(all_characters)
    log(f"DB 매칭: {len(matched)}명")

    # 결과 저장
    output_path = os.path.join(os.path.dirname(__file__), 'namuwiki_characters.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'characters': all_characters,
            'matched': matched
        }, f, ensure_ascii=False, indent=2)

    log(f"\n저장 완료: {output_path}")

    # 샘플 출력
    log("\n샘플 매칭 결과:")
    for m in matched[:20]:
        log(f"  {m['name_full']} → {m['new_korean']}")

    return all_characters, matched


if __name__ == "__main__":
    crawl_top_anime()
