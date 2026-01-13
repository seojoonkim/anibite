"""
한국어 제목 자동 업데이트 스크립트
상위 인기 애니메이션의 한국어 제목을 자동으로 검색하고 업데이트
"""
import sqlite3
import time
import sys

DB_PATH = 'anime.db'

# 사전 정의된 한국어 제목 (웹 검색 결과 기반)
KNOWN_TITLES = {
    # 이미 업데이트된 것들은 제외하고, 추가로 알려진 것들만
    137822: ('블루 락', True),  # Blue Lock
    127720: ('무직전생 ~이세계에 갔으면 최선을 다한다~ 2쿨', True),  # Mushoku Tensei Part 2
    116006: ('갓 오브 하이스쿨', True),  # The God of High School
    101165: ('고블린 슬레이어', True),  # Goblin Slayer
    164: ('모노노케 히메', True),  # Princess Mononoke
    116589: ('86 -에이티식스-', True),  # 86 Eighty-Six
    6746: ('뒤라라라!!', True),  # Durarara!!
    106625: ('하이큐!! TO THE TOP', True),  # Haikyu!! TO THE TOP
    102883: ('죠죠의 기묘한 모험: 황금의 바람', True),  # JoJo Golden Wind
    114236: ('염염소방대 2기', True),  # Fire Force Season 2
    124845: ('원더 에그 프라이어리티', True),  # Wonder Egg Priority
    99539: ('일곱 개의 대죄: 계명의 부활', True),  # Seven Deadly Sins: Revival of the Commandments
    119661: ('Re: 제로부터 시작하는 이세계 생활 2기 파트 2', True),  # Re:Zero Season 2 Part 2
    100182: ('소드 아트 온라인: 앨리시제이션', True),  # SAO: Alicization
    7054: ('회장님은 메이드 사마!', True),  # Maid-Sama!
    20661: ('잔향의 테러', True),  # Terror in Resonance
    20799: ('죠죠의 기묘한 모험: 스타더스트 크루세이더스 이집트편', True),  # JoJo Stardust Crusaders Egypt
    18153: ('경계의 저편', True),  # Beyond the Boundary
    8074: ('학원묵시록 HIGHSCHOOL OF THE DEAD', True),  # High School of the Dead
    125367: ('카구야 님은 고백받고 싶어 ~울트라 로맨틱~', True),  # Kaguya-sama Ultra Romantic
}

def update_korean_title(anime_id, korean_title, is_official):
    """데이터베이스에 한국어 제목 업데이트"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE anime
            SET title_korean = ?, title_korean_official = ?
            WHERE id = ?
        """, (korean_title, 1 if is_official else 0, anime_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ 업데이트 실패 (ID: {anime_id}): {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🔄 한국어 제목 자동 업데이트 시작")
    print("="*60 + "\n")

    updated_count = 0
    failed_count = 0

    for anime_id, (korean_title, is_official) in KNOWN_TITLES.items():
        print(f"[{anime_id}] {korean_title}")

        if update_korean_title(anime_id, korean_title, is_official):
            updated_count += 1
            print(f"  ✅ 업데이트 완료")
        else:
            failed_count += 1

        time.sleep(0.1)

    # 최종 통계
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean IS NOT NULL")
    total_with_korean = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
    total_official = cursor.fetchone()[0]
    conn.close()

    print("\n" + "="*60)
    print("✅ 업데이트 완료!")
    print("="*60)
    print(f"  이번 작업: {updated_count}개 성공, {failed_count}개 실패")
    print(f"  전체 통계:")
    print(f"    - 한국어 제목 보유: {total_with_korean}개")
    print(f"    - 오피셜 제목: {total_official}개")
    print(f"    - 남은 작업: {3000 - total_with_korean}개")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨")
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
