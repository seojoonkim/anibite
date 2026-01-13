"""
시리즈 제목 자동 전파
1기가 한국어로 번역된 경우 나머지 시즌들도 자동으로 번역
"""
import sqlite3
import re

DB_PATH = '/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db'

# 시즌 패턴
SEASON_PATTERNS = {
    # 영어 패턴
    r'\s+2nd\s+Season': ('2기', '2nd Season'),
    r'\s+3rd\s+Season': ('3기', '3rd Season'),
    r'\s+4th\s+Season': ('4기', '4th Season'),
    r'\s+5th\s+Season': ('5기', '5th Season'),
    r'\s+Season\s+2': ('시즌 2', 'Season 2'),
    r'\s+Season\s+3': ('시즌 3', 'Season 3'),
    r'\s+Season\s+4': ('시즌 4', 'Season 4'),
    r'\s+Season\s+5': ('시즌 5', 'Season 5'),
    r'\s+II\b': ('2기', 'II'),
    r'\s+III\b': ('3기', 'III'),
    r'\s+IV\b': ('4기', 'IV'),
    r'\s+V\b': ('5기', 'V'),
    r'\s+2\b': ('2기', '2'),
    r'\s+3\b': ('3기', '3'),
    r'\s+4\b': ('4기', '4'),
    r'\s+5\b': ('5기', '5'),
    r':\s+2': (': 2기', ': 2'),
    r':\s+3': (': 3기', ': 3'),
    r':\s+4': (': 4기', ': 4'),
    r':\s+5': (': 5기', ': 5'),

    # 일본어/로마자 패턴
    r'\s+2nd': ('2기', '2nd'),
    r'\s+3rd': ('3기', '3rd'),
    r'\s+Second': ('2기', 'Second'),
    r'\s+Third': ('3기', 'Third'),
    r'\s+Fourth': ('4기', 'Fourth'),
    r'\s+Fifth': ('5기', 'Fifth'),
}

# 특수 패턴 (제목 끝에 있는 것)
ENDING_PATTERNS = {
    r'\s+S2$': ('시즌 2', 'S2'),
    r'\s+S3$': ('시즌 3', 'S3'),
    r'\s+S4$': ('시즌 4', 'S4'),
    r'\s+Part\s+2$': ('파트 2', 'Part 2'),
    r'\s+Part\s+3$': ('파트 3', 'Part 3'),
}

def normalize_title(title):
    """제목 정규화 (비교용)"""
    if not title:
        return ""
    # 특수문자 제거 및 소문자화
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def extract_base_title(title):
    """
    시즌 표시를 제거한 기본 제목 추출
    예: "Re:Zero 2nd Season" -> "Re:Zero"
    """
    if not title:
        return title

    # 모든 패턴 제거
    base = title
    for pattern in list(SEASON_PATTERNS.keys()) + list(ENDING_PATTERNS.keys()):
        base = re.sub(pattern, '', base, flags=re.IGNORECASE)

    # 추가 정리
    base = re.sub(r'\s+', ' ', base).strip()
    base = re.sub(r'[\-:]\s*$', '', base).strip()

    return base

def find_season_info(title):
    """
    제목에서 시즌 정보 추출
    Returns: (base_title, season_marker_korean, season_marker_english)
    """
    if not title:
        return None, None, None

    # 모든 패턴 확인
    for pattern, (korean, english) in {**SEASON_PATTERNS, **ENDING_PATTERNS}.items():
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            base = extract_base_title(title)
            return base, korean, english

    return None, None, None

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n시리즈 제목 자동 전파 시작...\n")

    # 1. 공식 한국어 제목이 있는 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english, title_korean
        FROM anime
        WHERE title_korean_official = 1
        ORDER BY popularity DESC
    """)

    official_titles = cursor.fetchall()
    print(f"공식 한국어 제목: {len(official_titles)}개\n")

    # 2. 한국어 제목이 없는 모든 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english, title_korean, title_korean_official
        FROM anime
        WHERE title_korean_official = 0
        ORDER BY popularity DESC
    """)

    unofficial_titles = cursor.fetchall()
    print(f"공식 제목 없음: {len(unofficial_titles)}개\n")

    updated = 0

    # 3. 각 공식 제목에 대해 시리즈 탐색
    for official_id, official_romaji, official_english, official_korean in official_titles:
        # 기본 제목 추출
        base_romaji = extract_base_title(official_romaji) if official_romaji else ""
        base_english = extract_base_title(official_english) if official_english else ""
        base_korean = official_korean

        # 너무 짧은 제목은 스킵 (오매칭 방지)
        if len(base_romaji) < 3 and len(base_english) < 3:
            continue

        # 비공식 제목 중에서 시리즈 찾기
        for target_id, target_romaji, target_english, target_korean, target_official in unofficial_titles:
            if target_id == official_id:
                continue

            # 로마자 제목에서 시즌 정보 추출
            romaji_base, romaji_korean_season, romaji_english_season = find_season_info(target_romaji)
            english_base, english_korean_season, english_english_season = find_season_info(target_english) if target_english else (None, None, None)

            # 기본 제목이 일치하는지 확인
            is_match = False
            korean_season = None

            if romaji_base and normalize_title(romaji_base) == normalize_title(base_romaji):
                is_match = True
                korean_season = romaji_korean_season
            elif english_base and base_english and normalize_title(english_base) == normalize_title(base_english):
                is_match = True
                korean_season = english_korean_season

            if is_match and korean_season:
                # 한국어 제목 생성
                new_korean_title = f"{base_korean} {korean_season}"

                # 업데이트
                cursor.execute("""
                    UPDATE anime
                    SET title_korean = ?, title_korean_official = 1
                    WHERE id = ?
                """, (new_korean_title, target_id))

                print(f"🔵 {target_id}: {target_romaji} → {new_korean_title}")
                updated += 1

    conn.commit()

    # 현재 공식 제목 총 개수 확인
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
    total_official = cursor.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"시리즈 제목 전파 완료!")
    print(f"{'='*60}")
    print(f"  업데이트: {updated}개")
    print(f"  총 공식 제목: {total_official}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
