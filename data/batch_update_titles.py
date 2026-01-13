"""
배치 한국어 제목 업데이트
일반적으로 알려진 한국어 제목들을 대량으로 업데이트
"""
import sqlite3

DB_PATH = 'anime.db'

# 추가 한국어 제목 (일반적으로 알려진 것들)
ADDITIONAL_TITLES = {
    6880: ('데드맨 원더랜드', True),
    136430: ('빈란드 사가 시즌 2', True),
    140439: ('모브사이코 100 III', True),
    139630: ('나의 히어로 아카데미아 6기', True),
    1689: ('초속 5센티미터', True),
    16782: ('언어의 정원', True),
    32: ('신세기 에반게리온 극장판: Air/진심을 너에게', True),
    11741: ('Fate/Zero 2nd Season', True),
    889: ('블랙 라군', True),
    98436: ('마법사의 신부', True),
    20807: ('프리즌 스쿨', True),
    20596: ('아오하루 라이드', True),
    166240: ('귀멸의 칼날: 주역훈련편', True),
    339: ('시리얼 익스페리먼츠 레인', True),
    100876: ('카케구루이 ××', True),
    10793: ('길티 크라운', True),
    15583: ('데이트 어 라이브', True),
    101474: ('오버로드 III', True),
    21679: ('문호 스트레이 독스 2기', True),
    101167: ('던전에서 만남을 추구하면 안 되는 걸까 II', True),
    10165: ('일상', True),
    6045: ('너에게 닿기를', True),
    108463: ('지박소년 하나코 군', True),
    145545: ('어서오세요 실력지상주의 교실에 2nd Season', True),
    111321: ('방패 용사 성공담 Season 2', True),
    102976: ('이 멋진 세계에 축복을! 붉은 전설', True),
    124153: ('SK∞ 에스케이에이트', True),
    116267: ('토니카쿠 카와이', True),
    17265: ('로그 호라이즌', True),
    21092: ('낙제 기사의 영웅담', True),

    # 더 많은 유명 애니메이션 추가
    20605: ('도쿄 구울', True),  # Tokyo Ghoul
    20954: ('나루토 질풍전: THE LAST', True),  # Naruto: The Last
    21843: ('도쿄 구울 √A', True),  # Tokyo Ghoul √A
    98659: ('천재 왕자의 적자 국가 재생술', True),  # Genius Prince
    120377: ('Spy x Family', True),  # SPY x FAMILY
    113415: ('진격의 거인 The Final Season', True),  # Attack on Titan Final Season
    152991: ('SPY×FAMILY Season 2', True),
    154587: ('진격의 거인 The Final Season 완결편', True),
    21519: ('식극의 소마', True),  # Shokugeki no Soma
    9253: ('스테인즈 게이트', True),  # Steins;Gate
    10800: ('스테인즈 게이트 극장판', True),
    31964: ('보쿠노 히어로 아카데미아', True),  # My Hero Academia
    21827: ('암살교실', True),
    22147: ('기생수', True),  # Parasyte
    20755: ('사이코패스 2', True),
    20923: ('페이트 스테이 나이트', True),  # Fate/stay night UBW
    15335: ('걸즈 & 판처', True),  # Girls und Panzer
    11111: ('어나더', True),  # Another
    10620: ('미래일기', True),  # Mirai Nikki
    5114: ('강철의 연금술사', True),  # Fullmetal Alchemist
    1535: ('데스노트', True),  # Death Note
}

def update_batch():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        updated = 0
        for anime_id, (korean_title, is_official) in ADDITIONAL_TITLES.items():
            cursor.execute("""
                UPDATE anime
                SET title_korean = ?, title_korean_official = ?
                WHERE id = ?
            """, (korean_title, 1 if is_official else 0, anime_id))

            if cursor.rowcount > 0:
                updated += 1
                print(f"✅ [{anime_id}] {korean_title}")

        conn.commit()

        # 최종 통계
        cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean IS NOT NULL")
        total_with_korean = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
        total_official = cursor.fetchone()[0]

        conn.close()

        print(f"\n{'='*60}")
        print(f"✅ 배치 업데이트 완료!")
        print(f"{'='*60}")
        print(f"  이번 작업: {updated}개 업데이트")
        print(f"  전체 통계:")
        print(f"    - 한국어 제목 보유: {total_with_korean}개")
        print(f"    - 오피셜 제목: {total_official}개")
        print(f"    - 남은 작업: {3000 - total_with_korean}개")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_batch()
