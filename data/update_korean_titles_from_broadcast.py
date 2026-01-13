"""
한국 방영 애니메이션 제목 데이터로 데이터베이스 업데이트
korean_broadcast_anime.txt의 데이터를 사용하여 title_korean 업데이트
"""
import sqlite3

# 수동 수정이 필요한 잘못된 매칭 (이전에 확인한 것들)
MANUAL_CORRECTIONS = {
    21519: "너의 이름은",  # Kimi no Na wa (currently wrong)
    20755: "암살교실",  # Ansatsu Kyoushitsu
    199: "센과 치히로의 행방불명",  # Sen to Chihiro
    1575: "코드 기어스: 반역의 를루슈",  # Code Geass
    21827: "바이올렛 에버가든",  # Violet Evergarden
    20920: "식극의 소마",  # Shokugeki no Souma
    20464: "하이큐!!",  # Haikyuu!!
    120377: "사이버펑크: 엣지러너",  # Cyberpunk Edgerunners
    853: "오란고교 호스트부",  # Ouran Koukou Host Club
    813: "카드캡터 사쿠라",  # Cardcaptor Sakura
    16782: "언어의 정원",  # Kotonoha no Niwa
    9756: "마법소녀 마도카☆마기카",  # Mahou Shoujo Madoka Magica
}

def update_korean_titles():
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()

    print("📺 한국 방영 애니메이션 제목 데이터로 업데이트 시작...")

    # 파일에서 데이터 읽기
    with open('korean_broadcast_anime.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated_count = 0
    added_count = 0
    corrected_count = 0
    skipped_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split('|')
        if len(parts) < 3:
            continue

        anime_id = int(parts[0])
        korean_title = parts[1]
        romaji_title = parts[2]

        # 수동 수정 목록에 있으면 해당 제목 사용
        if anime_id in MANUAL_CORRECTIONS:
            korean_title = MANUAL_CORRECTIONS[anime_id]
            print(f"🔧 수동 수정: ID {anime_id} -> {korean_title}")

        # 현재 DB의 제목 확인
        cursor.execute(
            "SELECT title_korean, title_romaji FROM anime WHERE id = ?",
            (anime_id,)
        )
        row = cursor.fetchone()

        if not row:
            print(f"⚠️  ID {anime_id} not found in database")
            skipped_count += 1
            continue

        current_korean, current_romaji = row

        # 제목이 없으면 추가
        if not current_korean:
            cursor.execute(
                "UPDATE anime SET title_korean = ? WHERE id = ?",
                (korean_title, anime_id)
            )
            print(f"➕ ID {anime_id}: {current_romaji} -> 한국어 제목 추가: {korean_title}")
            added_count += 1
        # 제목이 다르면 수정
        elif current_korean != korean_title:
            cursor.execute(
                "UPDATE anime SET title_korean = ? WHERE id = ?",
                (korean_title, anime_id)
            )
            print(f"✏️  ID {anime_id}: {current_romaji}")
            print(f"   변경: {current_korean} -> {korean_title}")
            corrected_count += 1
        else:
            updated_count += 1

    conn.commit()
    conn.close()

    print(f"\n✅ 완료!")
    print(f"   - 이미 정확: {updated_count}개")
    print(f"   - 추가: {added_count}개")
    print(f"   - 수정: {corrected_count}개")
    print(f"   - 스킵: {skipped_count}개")
    print(f"   - 총 처리: {updated_count + added_count + corrected_count}개")

if __name__ == "__main__":
    update_korean_titles()
