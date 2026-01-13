"""
인기 애니메이션의 한국어 공식 제목 추가
"""
import sqlite3

DB_PATH = 'anime.db'

# 한국에서 공식적으로 사용되는 애니메이션 제목 (주요 인기작 위주)
KOREAN_TITLES = {
    # Attack on Titan
    'Shingeki no Kyojin': '진격의 거인',

    # Demon Slayer
    'Kimetsu no Yaiba': '귀멸의 칼날',

    # Death Note
    'DEATH NOTE': '데스노트',

    # Jujutsu Kaisen
    'Jujutsu Kaisen': '주술회전',

    # My Hero Academia
    'Boku no Hero Academia': '나의 히어로 아카데미아',

    # Hunter x Hunter
    'Hunter x Hunter': '헌터×헌터',
    'HUNTER×HUNTER': '헌터×헌터',

    # One Piece
    'ONE PIECE': '원피스',

    # Naruto
    'NARUTO': '나루토',
    'Naruto: Shippuuden': '나루토 질풍전',

    # Bleach
    'BLEACH': '블리치',

    # Fullmetal Alchemist
    'Hagane no Renkinjutsushi': '강철의 연금술사',
    'Fullmetal Alchemist: Brotherhood': '강철의 연금술사 BROTHERHOOD',

    # Steins;Gate
    'Steins;Gate': '슈타인즈 게이트',

    # Code Geass
    'Code Geass: Hangyaku no Lelouch': '코드 기아스 반역의 를르슈',

    # Sword Art Online
    'Sword Art Online': '소드 아트 온라인',

    # Tokyo Ghoul
    'Tokyo Ghoul': '도쿄 구울',

    # Cowboy Bebop
    'Cowboy Bebop': '카우보이 비밥',

    # Neon Genesis Evangelion
    'Shinseiki Evangelion': '신세기 에반게리온',

    # Spirited Away
    'Sen to Chihiro no Kamikakushi': '센과 치히로의 행방불명',

    # Your Name
    'Kimi no Na wa.': '너의 이름은.',

    # Weathering with You
    'Tenki no Ko': '날씨의 아이',

    # A Silent Voice
    'Koe no Katachi': '목소리의 형태',

    # Violet Evergarden
    'Violet Evergarden': '바이올렛 에버가든',

    # Made in Abyss
    'Made in Abyss': '메이드 인 어비스',

    # Re:Zero
    'Re:Zero kara Hajimeru Isekai Seikatsu': 'Re: 제로부터 시작하는 이세계 생활',

    # Mob Psycho 100
    'Mob Psycho 100': '모브사이코 100',

    # One Punch Man
    'One Punch Man': '원펀맨',

    # Haikyuu!!
    'Haikyuu!!': '하이큐!!',

    # Kuroko no Basket
    'Kuroko no Basket': '쿠로코의 농구',

    # Slam Dunk
    'Slam Dunk': '슬램덩크',

    # Dragon Ball
    'Dragon Ball': '드래곤볼',
    'Dragon Ball Z': '드래곤볼 Z',
    'Dragon Ball Super': '드래곤볼 슈퍼',

    # Pokemon
    'Pocket Monsters': '포켓몬스터',

    # Detective Conan
    'Meitantei Conan': '명탐정 코난',

    # Crayon Shin-chan
    'Crayon Shin-chan': '짱구는 못말려',

    # Doraemon
    'Doraemon': '도라에몽',

    # Spy x Family
    'SPY×FAMILY': '스파이 패밀리',

    # Chainsaw Man
    'Chainsaw Man': '체인소 맨',

    # Bocchi the Rock!
    'Bocchi the Rock!': '봇치 더 록!',

    # Frieren
    'Sousou no Frieren': '장송의 프리렌',

    # Oshi no Ko
    '【Oshi no Ko】': '최애의 아이',

    # Vinland Saga
    'Vinland Saga': '빈란드 사가',

    # Mushoku Tensei
    'Mushoku Tensei: Isekai Ittara Honki Dasu': '무직전생',

    # Overlord
    'Overlord': '오버로드',

    # That Time I Got Reincarnated as a Slime
    'Tensei shitara Slime Datta Ken': '전생했더니 슬라임이었던 건에 대하여',

    # The Rising of the Shield Hero
    'Tate no Yuusha no Nariagari': '방패 용사 성공담',

    # KonoSuba
    'Kono Subarashii Sekai ni Shukufuku wo!': '이 멋진 세계에 축복을!',

    # No Game No Life
    'No Game No Life': '노 게임 노 라이프',

    # The Promised Neverland
    'Yakusoku no Neverland': '약속의 네버랜드',

    # Dr. Stone
    'Dr. STONE': '닥터 스톤',

    # Fire Force
    'Enen no Shouboutai': '염염 소방대',

    # Black Clover
    'Black Clover': '블랙 클로버',

    # Fairy Tail
    'FAIRY TAIL': '페어리 테일',

    # Gintama
    'Gintama': '은혼',

    # Assassination Classroom
    'Ansatsu Kyoushitsu': '암살교실',

    # Parasyte
    'Kiseijuu: Sei no Kakuritsu': '기생수',

    # Another
    'Another': '어나더',

    # Erased
    'Boku dake ga Inai Machi': '나만이 없는 거리',

    # Angel Beats!
    'Angel Beats!': '엔젤 비트!',

    # Clannad
    'CLANNAD': '클라나드',

    # Toradora!
    'Toradora!': '토라도라!',

    # Your Lie in April
    'Shigatsu wa Kimi no Uso': '4월은 너의 거짓말',

    # Anohana
    'Ano Hi Mita Hana no Namae wo Bokutachi wa Mada Shiranai.': '그날 본 꽃의 이름을 우리는 아직 모른다',

    # Attack on Titan Season 2-4
    'Shingeki no Kyojin Season 2': '진격의 거인 Season 2',
    'Shingeki no Kyojin Season 3': '진격의 거인 Season 3',
    'Shingeki no Kyojin: The Final Season': '진격의 거인 The Final Season',
}

def update_korean_titles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("╔════════════════════════════════════════════════════════════╗")
    print("║   🌏 한국어 제목 업데이트                                  ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    updated = 0
    not_found = []

    for romaji_title, korean_title in KOREAN_TITLES.items():
        # Try exact match first
        cursor.execute("""
            SELECT id, title_romaji FROM anime
            WHERE title_romaji = ? OR title_english = ?
        """, (romaji_title, romaji_title))

        result = cursor.fetchone()

        if result:
            anime_id, title = result
            cursor.execute("""
                UPDATE anime
                SET title_korean = ?
                WHERE id = ?
            """, (korean_title, anime_id))

            updated += 1
            print(f"✓ {title} → {korean_title}")
        else:
            not_found.append(romaji_title)

    conn.commit()

    print(f"\n{'='*60}")
    print(f"✅ 업데이트 완료!")
    print(f"{'='*60}")
    print(f"  성공: {updated}개")
    print(f"  실패: {len(not_found)}개")

    if not_found:
        print(f"\n⚠️ 찾지 못한 애니메이션:")
        for title in not_found[:10]:
            print(f"  - {title}")

    conn.close()

if __name__ == '__main__':
    try:
        update_korean_titles()
    except Exception as e:
        print(f"\n❌ 에러: {e}")
