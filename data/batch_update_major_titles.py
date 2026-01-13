"""
주요 유명 애니메이션 한국어 제목 대량 업데이트
"""
import sqlite3

DB_PATH = 'anime.db'

# 주요 유명 애니메이션 한국어 제목
MAJOR_TITLES = {
    104578: ('진격의 거인 Season 3 Part 2', True),
    1735: ('나루토 질풍전', True),
    101921: ('카구야 님은 고백받고 싶어 ~천재들의 연애 두뇌전~', True),
    20789: ('일곱 개의 대죄', True),
    124080: ('호리미야', True),
    112151: ('귀멸의 칼날: 무한열차편', True),
    99423: ('달링 인 더 프랑키스', True),
    30: ('신세기 에반게리온', True),
    20931: ('데스 퍼레이드', True),
    14719: ('죠죠의 기묘한 모험', True),
    112641: ('카구야 님은 고백받고 싶어? ~천재들의 연애 두뇌전~', True),
    20997: ('샬롯', True),
    21311: ('문호 스트레이 독스', True),
    131681: ('진격의 거인: The Final Season Part 2', True),
    18679: ('킬라킬', True),
    20850: ('도쿄 구울 √A', True),
    117193: ('나의 히어로 아카데미아 5기', True),
    20992: ('하이큐!! 2nd Season', True),
    21804: ('사이키 쿠스오의 재난', True),
    14741: ('중2병이라도 사랑이 하고 싶어!', True),
    145139: ('귀멸의 칼날: 칼장이 마을편', True),
    129874: ('귀멸의 칼날: 무한열차편 (TV)', True),
    5081: ('바케모노가타리', True),
    20474: ('죠죠의 기묘한 모험: 스타더스트 크루세이더스', True),
    171018: ('단다단', True),
    115230: ('신의 탑', True),
    21776: ('코바야시네 메이드래곤', True),
    113936: ('닥터 스톤: STONE WARS', True),
    108725: ('약속의 네버랜드 2기', True),
    99578: ('사랑하기엔 너무 어색한', True),
    20829: ('종말의 세라프', True),
    19: ('몬스터', True),
    9756: ('마법소녀 마도카☆마기카', True),
    142838: ('SPY×FAMILY Part 2', True),
    21128: ('노라가미 ARAGOTO', True),
    128893: ('지옥낙원', True),
    100388: ('바나나 피쉬', True),
    130298: ('그림자 실력자가 되고 싶어서!', True),
    523: ('이웃집 토토로', True),
    13759: ('사쿠라장의 애완 그녀', True),
    5680: ('케이온!', True),
    205: ('사무라이 참프루', True),
    226: ('엘펜리트', True),
    161645: ('약사의 혼잣말', True),
    20698: ('역시 내 청춘 러브코메디는 잘못됐다. 속', True),
    18897: ('니세코이', True),
    21518: ('식극의 소마: 이노사라', True),
    120697: ('놀리지 마요, 나가토로 양', True),
    19603: ('Fate/stay night: Unlimited Blade Works', True),
    176496: ('나 혼자만 레벨업: Season 2 - Arise from the Shadow', True),

    # 더 많은 유명 애니메이션
    31964: ('나의 히어로 아카데미아', True),
    21843: ('도쿄 구울 √A', True),
    22147: ('기생수', True),
    20755: ('PSYCHO-PASS 2', True),
    31043: ('아오하루 라이드 OVA', True),
    111413: ('바쿠간', True),
    31771: ('코노스바 OVA', True),
    28121: ('던전에서 만남을 추구하면 안 되는 걸까 OVA', True),
    28223: ('소드 아트 온라인 II -데바울 불릿-', True),
    98578: ('하이스쿨 D×D HERO', True),
    106995: ('메이드 인 어비스: 깊은 영혼의 여명', True),
    20912: ('페이트 스테이 나이트: 언리미티드 블레이드 워크스', True),
    13125: ('이 중에 1명, 여동생이 있다!', True),
    16498: ('진격의 거인', True),
    18507: ('물의 여정 ~아리에티~', True),
    11887: ('코쿠리코 언덕에서', True),
    312: ('바람계곡의 나우시카', True),
    572: ('마녀 배달부 키키', True),
    22587: ('바람이 분다', True),
    136: ('헌터X헌터', True),
    20: ('나루토', True),
    6702: ('페어리 테일', True),
    269: ('블리치', True),
    813: ('은혼', True),
    1: ('카우보이 비밥', True),
    5: ('카우보이 비밥: 천국의 문', True),
    170: ('일곱 개의 대죄 OVA', True),
}

def update_batch():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        updated = 0
        for anime_id, (korean_title, is_official) in MAJOR_TITLES.items():
            cursor.execute("""
                UPDATE anime
                SET title_korean = ?, title_korean_official = ?
                WHERE id = ?
            """, (korean_title, 1 if is_official else 0, anime_id))

            if cursor.rowcount > 0:
                updated += 1

        conn.commit()

        # 최종 통계
        cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean IS NOT NULL")
        total_with_korean = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
        total_official = cursor.fetchone()[0]

        conn.close()

        print(f"{'='*60}")
        print(f"✅ 주요 애니메이션 제목 업데이트 완료!")
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
