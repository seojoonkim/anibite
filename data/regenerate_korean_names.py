#!/usr/bin/env python3
"""
영어 이름 → 한국어 발음 변환 (개선 버전)
- 중간점(·) 대신 공백 사용
- 원어 발음 기반 (일본식 발음 X)
- 음절 단위 변환
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db


def log(msg):
    print(msg, flush=True)


# 영어 음절 → 한국어 변환 (긴 패턴 우선)
SYLLABLE_MAP = [
    # 특수 이름/단어 패턴 (자주 나오는 것들)
    ('krueger', '크루거'),
    ('yeager', '예거'),
    ('jaeger', '예거'),
    ('kruger', '크루거'),
    ('ackerman', '아커만'),
    ('acker', '아커'),
    ('tucker', '터커'),
    ('walker', '워커'),
    ('miller', '밀러'),
    ('hunter', '헌터'),
    ('winter', '윈터'),
    ('smith', '스미스'),
    ('jones', '존스'),
    ('brown', '브라운'),
    ('green', '그린'),
    ('white', '화이트'),
    ('black', '블랙'),
    ('young', '영'),
    ('monkey', '몽키'),
    ('luffy', '루피'),
    ('power', '파워'),
    ('eren', '에렌'),
    ('levi', '리바이'),
    ('guts', '가츠'),
    ('light', '라이트'),
    ('edward', '에드워드'),
    ('frieren', '프리렌'),

    # 일본 이름 패턴 (자주 나오는 것들)
    ('toru', '토루'),
    ('oru', '오루'),
    ('aru', '아루'),
    ('iru', '이루'),
    ('uru', '우루'),
    ('suke', '스케'),
    ('maki', '마키'),
    ('saki', '사키'),
    ('kawa', '카와'),
    ('yama', '야마'),
    ('mura', '무라'),
    ('shima', '시마'),
    ('hara', '하라'),
    ('uchi', '우치'),
    ('naka', '나카'),
    ('jima', '지마'),

    # -tion, -sion
    ('tion', '션'),
    ('sion', '전'),

    # -er/-or/-ar 끝나는 패턴
    ('cher', '쳐'),
    ('sher', '셔'),
    ('ther', '더'),
    ('pher', '퍼'),
    ('ger', '거'),
    ('ler', '러'),
    ('ner', '너'),
    ('ter', '터'),
    ('der', '더'),
    ('ber', '버'),
    ('per', '퍼'),
    ('ker', '커'),
    ('ver', '버'),
    ('ser', '서'),
    ('zer', '저'),
    ('fer', '퍼'),
    ('mer', '머'),
    ('wer', '워'),
    ('rer', '러'),

    # -or
    ('tor', '토르'),
    ('dor', '도르'),
    ('nor', '노르'),
    ('gor', '고르'),

    # -ar
    ('tar', '타르'),
    ('sar', '사르'),
    ('lar', '라르'),
    ('nar', '나르'),
    ('mar', '마르'),
    ('kar', '카르'),

    # -ing
    ('ring', '링'),
    ('king', '킹'),
    ('sing', '싱'),
    ('ting', '팅'),
    ('ning', '닝'),
    ('ming', '밍'),
    ('ling', '링'),
    ('ping', '핑'),
    ('ding', '딩'),
    ('bing', '빙'),
    ('wing', '윙'),
    ('zing', '징'),

    # 이중모음/장모음
    ('ough', '오'),
    ('augh', '오'),
    ('ight', '아이트'),
    ('eigh', '에이'),
    ('ould', '우드'),

    # -ck, -tch
    ('tch', '치'),
    ('ck', '크'),

    # 자음군
    ('sch', '슈'),
    ('scr', '스크'),
    ('spr', '스프'),
    ('str', '스트'),
    ('squ', '스퀘'),
    ('thr', '스'),
    ('chr', '크'),
    ('shr', '슈'),
    ('wh', '와'),
    ('wr', ''),
    ('kn', '나'),
    ('gn', '나'),
    ('ph', '프'),
    ('gh', ''),
    ('ng', '응'),
    ('nk', '잉크'),
    ('qu', '퀘'),
    ('th', '스'),
    ('sh', '쉬'),
    ('ch', '츠'),

    # 자음+모음 조합 (가장 일반적인 패턴)
    # Ca Ce Ci Co Cu
    ('ca', '카'),
    ('ce', '세'),
    ('ci', '시'),
    ('co', '코'),
    ('cu', '쿠'),
    ('cy', '시'),

    # Ga Ge Gi Go Gu
    ('ga', '가'),
    ('ge', '게'),
    ('gi', '기'),
    ('go', '고'),
    ('gu', '구'),
    ('gy', '지'),

    # 일반 자음+모음
    ('ba', '바'), ('be', '베'), ('bi', '비'), ('bo', '보'), ('bu', '부'), ('by', '바이'),
    ('da', '다'), ('de', '데'), ('di', '디'), ('do', '도'), ('du', '두'), ('dy', '디'),
    ('fa', '파'), ('fe', '페'), ('fi', '피'), ('fo', '포'), ('fu', '푸'), ('fy', '파이'),
    ('ha', '하'), ('he', '헤'), ('hi', '히'), ('ho', '호'), ('hu', '후'), ('hy', '하이'),
    ('ja', '자'), ('je', '제'), ('ji', '지'), ('jo', '조'), ('ju', '주'), ('jy', '지'),
    ('ka', '카'), ('ke', '케'), ('ki', '키'), ('ko', '코'), ('ku', '쿠'), ('ky', '키'),
    ('la', '라'), ('le', '레'), ('li', '리'), ('lo', '로'), ('lu', '루'), ('ly', '리'),
    ('ma', '마'), ('me', '메'), ('mi', '미'), ('mo', '모'), ('mu', '무'), ('my', '마이'),
    ('na', '나'), ('ne', '네'), ('ni', '니'), ('no', '노'), ('nu', '누'), ('ny', '니'),
    ('pa', '파'), ('pe', '페'), ('pi', '피'), ('po', '포'), ('pu', '푸'), ('py', '파이'),
    ('ra', '라'), ('re', '레'), ('ri', '리'), ('ro', '로'), ('ru', '루'), ('ry', '리'),
    ('sa', '사'), ('se', '세'), ('si', '시'), ('so', '소'), ('su', '수'), ('sy', '시'),
    ('ta', '타'), ('te', '테'), ('ti', '티'), ('to', '토'), ('tu', '투'), ('ty', '티'),
    ('va', '바'), ('ve', '베'), ('vi', '비'), ('vo', '보'), ('vu', '부'), ('vy', '비'),
    ('wa', '와'), ('we', '웨'), ('wi', '위'), ('wo', '워'), ('wu', '우'), ('wy', '와이'),
    ('xa', '자'), ('xe', '제'), ('xi', '지'), ('xo', '조'), ('xu', '주'),
    ('ya', '야'), ('ye', '예'), ('yi', '이'), ('yo', '요'), ('yu', '유'),
    ('za', '자'), ('ze', '제'), ('zi', '지'), ('zo', '조'), ('zu', '주'), ('zy', '지'),

    # 이중모음
    ('ai', '아이'),
    ('ay', '에이'),
    ('ea', '이'),
    ('ee', '이'),
    ('ei', '에이'),
    ('ey', '이'),
    ('ie', '이'),
    ('oa', '오'),
    ('oe', '오'),
    ('oi', '오이'),
    ('oo', '우'),
    ('ou', '아우'),
    ('ow', '오'),
    ('oy', '오이'),
    ('ue', '유'),
    ('ui', '위'),

    # 단독 자음 (단어 끝)
    ('b', '브'),
    ('c', '크'),
    ('d', '드'),
    ('f', '프'),
    ('g', '그'),
    ('h', ''),
    ('j', '즈'),
    ('k', '크'),
    ('l', '르'),
    ('m', '므'),
    ('n', '느'),
    ('p', '프'),
    ('r', '르'),
    ('s', '스'),
    ('t', '트'),
    ('v', '브'),
    ('w', ''),
    ('x', '스'),
    ('z', '즈'),

    # 단독 모음
    ('a', '아'),
    ('e', '에'),
    ('i', '이'),
    ('o', '오'),
    ('u', '우'),
    ('y', '이'),
]


def english_to_korean(name):
    """영어 이름을 한국어 발음으로 변환"""
    if not name:
        return None

    # 소문자로
    text = name.lower()
    result = ''
    i = 0

    while i < len(text):
        if text[i] == ' ':
            result += ' '
            i += 1
            continue

        if not text[i].isalpha():
            i += 1
            continue

        matched = False
        # 긴 패턴부터 매칭
        for pattern, korean in SYLLABLE_MAP:
            if text[i:].startswith(pattern):
                result += korean
                i += len(pattern)
                matched = True
                break

        if not matched:
            i += 1

    # 정리
    result = re.sub(r'\s+', ' ', result).strip()

    return result if result else None


def regenerate_all_korean_names():
    """모든 캐릭터의 한국어 이름 재생성"""

    log("=" * 80)
    log("한국어 이름 재생성 (공백 사용, 원어 발음 기반)")
    log("=" * 80)

    # 영어 이름이 있는 모든 캐릭터 가져오기
    characters = db.execute_query("""
        SELECT id, name_full, name_native
        FROM character
        WHERE name_full IS NOT NULL AND name_full != ''
        ORDER BY favourites DESC
    """)

    log(f"\n총 {len(characters)}개 캐릭터 처리 예정")

    success_count = 0
    korean_names = {}

    for i, char in enumerate(characters):
        char_id = char['id']
        name_full = char['name_full']

        # 영어 이름을 한국어로 변환
        korean_name = english_to_korean(name_full)

        if korean_name and len(korean_name) >= 2:
            # 한글 비율 체크
            korean_chars = len(re.findall(r'[가-힣]', korean_name))
            total_chars = len(korean_name.replace(' ', ''))

            if total_chars > 0 and korean_chars / total_chars >= 0.5:
                korean_names[str(char_id)] = korean_name
                success_count += 1

                if i < 30:
                    log(f"[{i+1}] {name_full} → {korean_name}")

        if (i + 1) % 10000 == 0:
            log(f"Progress: {i+1}/{len(characters)}")

    log(f"\n변환 완료: {success_count}/{len(characters)}")

    # JSON으로 저장
    output_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'scripts', 'korean_names.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(korean_names, f, ensure_ascii=False, indent=None)

    log(f"저장 완료: {output_path}")
    log(f"파일 크기: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

    return korean_names


def test_samples():
    """샘플 테스트"""
    samples = [
        "Eren Krueger",
        "Eren Yeager",
        "Satoru Gojo",
        "Mikasa Ackerman",
        "Naruto Uzumaki",
        "Light Yagami",
        "Edward Elric",
        "Monkey D. Luffy",
        "Roronoa Zoro",
        "Izuku Midoriya",
        "Katsuki Bakugo",
        "Levi Ackerman",
        "Guts",
        "Frieren",
    ]

    log("샘플 테스트:")
    for name in samples:
        korean = english_to_korean(name)
        log(f"  {name} → {korean}")


if __name__ == "__main__":
    test_samples()
    log("\n" + "=" * 80)
    regenerate_all_korean_names()
