"""
나무위키에서 수집한 한국어 제목 업데이트
데이터베이스의 로마자 제목과 매칭
"""
import sqlite3
import re

# 나무위키에서 수집한 한국어 제목과 예상 로마자 제목 매칭
NAMU_TITLES = {
    # ㄱ 초성
    '가정교사 히트맨 REBORN!': ['Katekyo Hitman Reborn', 'REBORN!'],
    '간츠': ['Gantz'],
    '갑철성의 카바네리': ['Koutetsujou no Kabaneri', 'Kabaneri'],
    '건슬링거 걸': ['Gunslinger Girl'],

    # ㄴ 초성
    '나나': ['NANA'],
    '노다메 칸타빌레': ['Nodame Cantabile'],

    # ㄷ 초성
    '다이쇼 야구 소녀': ['Taishou Yakyuu Musume'],
    '도라에몽': ['Doraemon'],
    '도로로': ['Dororo'],
    '디지몬 어드벤처': ['Digimon Adventure'],
    '디그레이맨': ['D.Gray-man'],

    # ㄹ 초성
    '란마 1/2': ['Ranma'],
    '러브히나': ['Love Hina'],
    '로젠 메이든': ['Rozen Maiden'],
    '루팡 3세': ['Lupin'],
    '리라이프': ['ReLIFE'],
    '리틀 버스터즈!': ['Little Busters'],

    # ㅁ 초성
    '명탐정 코난': ['Detective Conan', 'Meitantei Conan'],
    '모노노케 히메': ['Mononoke Hime', 'Princess Mononoke'],
    '마법기사 레이어스': ['Magic Knight Rayearth'],
    '마법선생 네기마!': ['Negima'],
    '모브사이코 100': ['Mob Psycho 100'],
    '마기': ['Magi'],

    # ㅎ 초성
    '하울의 움직이는 성': ['Howl', 'Moving Castle'],
    '하야테처럼!': ['Hayate no Gotoku', 'Hayate the Combat Butler'],
    '흑집사': ['Kuroshitsuji', 'Black Butler'],
    '헤타리아': ['Hetalia'],
    '혈계전선': ['Kekkai Sensen', 'Blood Blockade Battlefront'],
    '허니와 클로버': ['Honey and Clover', 'Hachimitsu to Clover'],
    '학생회의 일존': ['Seitokai no Ichizon'],
    '학원묵시록: HIGHSCHOOL OF THE DEAD': ['Gakuen Mokushiroku', 'Highschool of the Dead'],
    '호오즈키의 냉철': ['Hoozuki no Reitetsu'],

    # 추가 인기작
    '포켓몬스터': ['Pokemon'],
    '풀 메탈 패닉': ['Full Metal Panic'],
    '프리큐어': ['Precure', 'Pretty Cure'],
    '플라스틱 메모리즈': ['Plastic Memories'],
    '펀치라인': ['Punchline'],
    '펌프킨 시저스': ['Pumpkin Scissors'],
    '페르소나': ['Persona'],
    '표류교실': ['Hyouryuu Kyoushitsu'],
    '푸른 강철의 아르페지오': ['Arpeggio', 'Blue Steel'],

    # 지브리 작품들
    '벼랑 위의 포뇨': ['Gake no Ue no Ponyo', 'Ponyo'],
    '이웃집 토토로': ['Tonari no Totoro', 'Totoro'],
    '센과 치히로의 행방불명': ['Sen to Chihiro', 'Spirited Away'],
    '마녀 배달부 키키': ['Majo no Takkyuubin'],
    '붉은 돼지': ['Kurenai no Buta', 'Porco Rosso'],
    '모노노케 히메': ['Mononoke Hime'],
}

def fuzzy_match(korean_title, romaji_or_english):
    """
    한국어 제목과 로마자/영어 제목의 유사도 확인
    """
    romaji_lower = romaji_or_english.lower()
    keywords = NAMU_TITLES.get(korean_title, [])

    for keyword in keywords:
        if keyword.lower() in romaji_lower:
            return True
    return False

def main():
    conn = sqlite3.connect('/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db')
    cursor = conn.cursor()

    print(f"\n나무위키 제목 {len(NAMU_TITLES)}개 매칭 시작...\n")

    # 데이터베이스에서 한국어 제목이 공식이 아닌 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english, title_korean
        FROM anime
        WHERE title_korean_official = 0
        ORDER BY popularity DESC
    """)

    anime_list = cursor.fetchall()

    updated = 0

    for korean_title, keywords in NAMU_TITLES.items():
        matched = False

        for anime_id, romaji, english, current_korean in anime_list:
            # 로마자 또는 영어 제목에서 키워드 매칭
            found = False
            for keyword in keywords:
                if keyword.lower() in (romaji or '').lower() or keyword.lower() in (english or '').lower():
                    found = True
                    break

            if found:
                # 업데이트
                cursor.execute("""
                    UPDATE anime
                    SET title_korean = ?, title_korean_official = 1
                    WHERE id = ?
                """, (korean_title, anime_id))

                print(f"🔵 {anime_id}: {romaji} → {korean_title}")
                updated += 1
                matched = True
                break

        if not matched:
            # 데이터베이스에 없음
            pass

    conn.commit()

    # 현재 공식 제목 총 개수 확인
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
    total_official = cursor.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"나무위키 제목 매칭 완료!")
    print(f"{'='*60}")
    print(f"  업데이트: {updated}개")
    print(f"  총 공식 제목: {total_official}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
