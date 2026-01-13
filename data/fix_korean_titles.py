"""
한국어 제목 매칭 오류 수정
잘못 매칭된 한국어 제목을 수동으로 수정
"""
import sqlite3

# 수정할 매칭 (anime_id: correct_korean_title)
CORRECTIONS = {
    # 잘못 매칭된 것들
    21519: "너의 이름은",  # Kimi no Na wa (currently: 식극의 소마)
    20755: "암살교실",  # Ansatsu Kyoushitsu (currently: 사쿠라 좀비)
    199: "센과 치히로의 행방불명",  # Sen to Chihiro (currently: 카레이도 스타)
    1575: "코드 기어스: 반역의 를루슈",  # Code Geass (currently: 테니스의 왕자)
    21827: "바이올렛 에버가든",  # Violet Evergarden (currently: 암살교실)
    20920: "식극의 소마",  # Shokugeki no Souma (currently: 페이트 스테이 나이트)
    20464: "하이큐!!",  # Haikyuu!! (currently: 쿠로코의 농구: 윈터컵 총집편)
    120377: "사이버펑크: 엣지러너", # Cyberpunk Edgerunners (currently: Spy x Family)
    853: "오란고교 호스트부",  # Ouran Koukou Host Club (currently: 아즈망가 대왕)
    813: "카드캡터 사쿠라",  # Cardcaptor Sakura (currently 드래곤볼Z로 잘못됨)
    16782: "언어의 정원",  # Kotonoha no Niwa (currently: 기동전사 건담 철혈의 오펀스)

    # 추가로 정확한 제목으로 수정
    9756: "마법소녀 마도카☆마기카",  # Mahou Shoujo Madoka Magica (currently: 메이저 6)
}

def fix_titles():
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()

    print("🔧 한국어 제목 수정 시작...")

    for anime_id, correct_title in CORRECTIONS.items():
        # 현재 제목 확인
        cursor.execute(
            "SELECT title_romaji, title_korean FROM anime WHERE id = ?",
            (anime_id,)
        )
        row = cursor.fetchone()

        if row:
            romaji, current_korean = row
            print(f"✏️  ID {anime_id}: {romaji}")
            print(f"   변경전: {current_korean}")
            print(f"   변경후: {correct_title}")

            # 업데이트
            cursor.execute(
                "UPDATE anime SET title_korean = ? WHERE id = ?",
                (correct_title, anime_id)
            )
        else:
            print(f"❌ ID {anime_id} not found")

    conn.commit()
    conn.close()

    print(f"\n✅ {len(CORRECTIONS)}개 제목 수정 완료!")

if __name__ == "__main__":
    fix_titles()
