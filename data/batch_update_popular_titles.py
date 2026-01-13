"""
추가 유명 애니메이션 한국어 제목 업데이트
"""
import sqlite3

DB_PATH = 'anime.db'

# 추가 유명 애니메이션 한국어 제목
POPULAR_TITLES = {
    151801: ('마슈르', True),  # MASHLE
    98437: ('오버로드 II', True),  # Overlord II
    107660: ('비스타즈', True),  # BEASTARS
    4898: ('흑집사', True),  # Black Butler
    21613: ('유녀전기', True),  # Saga of Tanya the Evil
    14227: ('이웃집 괴물군', True),  # My Little Monster
    17895: ('골든 타임', True),  # Golden Time
    112301: ('마왕학원의 부적합자 ~사상 최강의 마왕의 시조, 전생하여 자손들의 학교에 다니다~', True),
    20458: ('마법과 고교의 열등생', True),  # The Irregular at Magic High School
    20872: ('플라스틱 메모리즈', True),  # Plastic Memories
    113538: ('하이큐!! TO THE TOP 2부', True),
    853: ('오란고교 호스트부', True),  # Ouran High School Host Club
    141391: ('밤을 걷는 노래', True),  # Call of the Night
    104157: ('청춘 돼지는 꿈꾸는 소녀의 꿈을 꾸지 않는다', True),
    21049: ('리라이프', True),  # ReLIFE
    116742: ('전생했더니 슬라임이었던 건에 대하여 2기 파트 2', True),
    153288: ('괴수 8호', True),  # Kaiju No. 8
    437: ('퍼펙트 블루', True),  # Perfect Blue
    21857: ('마사무네 군의 리벤지', True),  # Masamune-kun's Revenge
    21647: ('오렌지', True),  # Orange
    21709: ('유리!!! 온 아이스', True),  # Yuri!!! on ICE
    16592: ('단간론파 희망의 학원과 절망의 고교생', True),  # Danganronpa
    102351: ('도쿄 구울:re 2기', True),  # Tokyo Ghoul:re 2
    146065: ('무직전생 ~이세계에 갔으면 최선을 다한다~ II', True),
    14513: ('마기 The labyrinth of magic', True),  # Magi
    99255: ('식극의 소마: 찬노사라', True),  # Food Wars! Third Plate
    21875: ('노 게임 노 라이프 제로', True),  # No Game No Life Zero
    110349: ('그레이트 프리텐더', True),  # Great Pretender
    146984: ('진격의 거인: The Final Season 완결편 전편', True),
    20727: ('혈계전선', True),  # Blood Blockade Battlefront
    47: ('아키라', True),  # AKIRA
    20668: ('월간소녀 노자키 군', True),  # Monthly Girls' Nozaki-kun
    97938: ('보루토: 나루토 넥스트 제너레이션즈', True),  # Boruto
    100922: ('그랑블루', True),  # Grand Blue
    159831: ('좀비가 되기까지 하고 싶은 100가지', True),  # Zom 100
    4181: ('클라나드: 애프터 스토리', True),  # Clannad: After Story
    100723: ('나의 히어로 아카데미아 더 무비: 두 명의 영웅', True),
    109261: ('5등분의 신부 ∬', True),
    21127: ('슈타인즈 게이트 제로', True),  # Steins;Gate 0
    103139: ('가정교사 히트맨 리본!', True),  # Domestic Girlfriend
    99629: ('살육의 천사', True),  # Angels of Death
    113717: ('왕님 랭킹', True),  # Ranking of Kings
    108489: ('역시 내 청춘 러브코메디는 잘못됐다. 완', True),
    108759: ('소드 아트 온라인: 앨리시제이션 - War of Underworld', True),
    100668: ('평범한 직업으로 세계 최강', True),  # Arifureta
    158927: ('SPY×FAMILY Season 2', True),
    21366: ('3월의 라이온', True),  # March comes in like a lion
    20770: ('새벽의 연화', True),  # Yona of the Dawn
    108430: ('기븐', True),  # given
    129201: ('섬머 타임 렌더', True),  # Summer Time Rendering
    100977: ('일하는 세포', True),  # Cells at Work!
    227: ('FLCL', True),  # FLCL
    20792: ('Fate/stay night: Unlimited Blade Works 2nd Season', True),
    20910: ('시모네타', True),  # SHIMONETA
    21421: ('킬즈나이버', True),  # Kiznaiver
    143270: ('리코리스 리코일', True),  # Lycoris Recoil
    131646: ('바니타스의 수기', True),  # The Case Study of Vanitas
    108928: ('일곱 개의 대죄: 신들의 역린', True),
    153518: ('던전 밥', True),  # Delicious in Dungeon
    127911: ('시키모리는 그저 귀엽기만 한 게 아니야', True),
    849: ('스즈미야 하루히의 우울', True),  # The Melancholy of Haruhi Suzumiya
    101004: ('이세계 마왕과 소환 소녀의 노예 마술', True),
    155783: ('천국대마경', True),  # Tengoku Daimakyo
    103223: ('문호 스트레이 독스 3기', True),
    21711: ('91 데이즈', True),  # 91 Days
    877: ('나나', True),  # NANA
    10408: ('반딧불이의 숲으로', True),  # Into the Forest of Fireflies' Light
    20457: ('블랙 불릿', True),  # Black Bullet
    578: ('반딧불이의 묘', True),  # Grave of the Fireflies
    20993: ('종말의 세라프: 나고야 결전편', True),
    12355: ('늑대아이', True),  # Wolf Children
    98291: ('츠레즈레 칠드런', True),  # Tsuredure Children
    15451: ('하이스쿨 D×D NEW', True),
    103047: ('바이올렛 에버가든: 극장판', True),
    112124: ('던전에서 만남을 추구하면 안 되는 걸까 III', True),
    21403: ('소드 아트 온라인: 오디널 스케일', True),
    11843: ('남자 고등학생의 일상', True),  # Daily Lives of High School Boys
    20631: ('트리니티 세븐', True),  # Trinity Seven
    1210: ('N.H.K에 어서오세요!', True),  # Welcome to the N-H-K
    21196: ('갑철성의 카바네리', True),  # Kabaneri of the Iron Fortress
    21700: ('바보와 시험과 소환수', True),  # Akashic Records
    105156: ('신중용사 ~이 용사가 TUEEE인 주제에 신중하다~', True),
    2251: ('바카노!', True),  # Baccano!
    114308: ('소드 아트 온라인: 앨리시제이션 War of Underworld 파트 2', True),
    457: ('무시시', True),  # Mushishi
    20994: ('게이트: 자위대. 그의 땅에서, 이처럼 싸우며', True),  # Gate
    21595: ('사카모토입니다만?', True),  # Haven't You Heard? I'm Sakamoto
    4654: ('어떤 마술의 금서목록', True),  # A Certain Magical Index
    177709: ('사카모토 데이즈', True),  # SAKAMOTO DAYS
    11597: ('니세모노가타리', True),  # Nisemonogatari
    21685: ('에로망가 선생', True),  # Eromanga Sensei
    131518: ('닥터 스톤: NEW WORLD', True),
    20966: ('야마다 군과 7인의 마녀', True),  # Yamada and the Seven Witches
    129898: ('세계 최고의 암살자, 이세계 귀족으로 전생한다', True),
    116674: ('블리치: 천년혈전편', True),  # BLEACH: Thousand-Year Blood War
    114232: ('수염을 깎다. 그리고 여고생을 줍다.', True),  # Higehiro
    185660: ('단다단 시즌 2', True),
    356: ('Fate/stay night', True),
    111762: ('후르츠 바스켓: 2nd Season', True),
    98034: ('사이키 쿠스오의 재난 2기', True),
}

def update_batch():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        updated = 0
        for anime_id, (korean_title, is_official) in POPULAR_TITLES.items():
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
        print(f"✅ 추가 인기 애니메이션 제목 업데이트 완료!")
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
