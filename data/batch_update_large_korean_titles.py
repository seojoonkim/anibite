"""
한국어 제목 대량 배치 업데이트
인기 애니메이션 200개
"""
import sqlite3

# 한국어 제목 매핑 (anime_id: (korean_title, is_official))
# True = 공식 한국어 제목, False = 번역/음역
KOREAN_TITLES = {
    # 이미 추가된 것들
    20626: ('페어리 테일', True),
    114963: ('울고 싶은 나는 고양이 가면을 쓴다', True),
    97994: ('블렌드 S', True),
    142770: ('스즈메의 문단속', True),

    # 지브리 & 유명 극장판
    2890: ('벼랑 위의 포뇨', True),
    512: ('마녀 배달부 키키', True),
    2236: ('시간을 달리는 소녀', True),

    # 청춘/로맨스
    21701: ('쓰레기의 본망', True),
    18671: ('중2병이라도 사랑이 하고 싶어! 연', True),
    154965: ('야마다 군과 Lv999의 사랑을 한다', True),
    21058: ('빨강머리 백설공주', True),
    20987: ('건어물 여동생! 우마루짱', True),
    99426: ('우주보다 먼 곳', True),
    99468: ('능숙한 장난 타카기 양', True),
    21093: ('몬스터 아가씨가 있는 일상', True),
    98444: ('유루캠프', True),

    # 판타지/이세계
    2966: ('늑대와 향신료', True),
    21428: ('회색도시 그림가르', True),
    166873: ('무직전생 II 이세계에 갔으면 최선을 다한다 Part 2', True),
    106479: ('방어력에 올인하고 싶어', True),
    100112: ('현자의 손자', True),
    21385: ('일곱 개의 대죄: 성전의 표적', True),

    # 액션/배틀
    131942: ('죠죠의 기묘한 모험 스톤 오션', True),
    16894: ('쿠로코의 농구 2기', True),
    131586: ('86 에이티식스 Part 2', True),
    21861: ('청의 엑소시스트 교토 부정왕편', True),
    777: ('헬싱 OVA', True),
    934: ('쓰르라미 울 적에', True),
    109963: ('식극의 소마 신의 접시', True),
    105228: ('도로헤도로', True),
    2025: ('다크 댄 블랙: 흑의 계약자', True),
    97922: ('이누야시키', True),
    108553: ('나의 히어로 아카데미아 더 무비: 히어로즈 라이징', True),
    249: ('이누야샤', True),
    33: ('베르세르크', True),
    43: ('공각기동대', True),
    245: ('지티오', True),
    14467: ('K', True),
    97766: ('게이머즈!', True),
    105190: ('다윈즈 게임', True),

    # SF/사이버펑크
    128546: ('Vivy: Fluorite Eye\'s Song', True),
    131565: ('takt op.Destiny', True),
    100183: ('소드 아트 온라인 얼터너티브 건 게일 온라인', True),

    # 스포츠/음식
    124194: ('후르츠 바스켓: 더 파이널', True),
    100773: ('식극의 소마 3기: 토츠키 열차편', True),
    113596: ('조제, 호랑이 그리고 물고기들', True),

    # 판타지/SF
    178025: ('가치악타', True),
    20657: ('시원찮은 그녀를 위한 육성방법', True),
    161964: ('실력으로는 그림자 되고 싶어! 2기', True),
    18115: ('마기: 더 킹덤 오브 매직', True),
    163270: ('윈드 브레이커', True),
    162804: ('가끔 러시아어로 속삭이는 옆자리 알랴 양', True),

    # 추가 대중적 애니메이션
    20: ('나루토', True),  # Naruto
    16498: ('진격의 거인', True),  # Shingeki no Kyojin
    1535: ('데스노트', True),  # Death Note
    11061: ('헌터X헌터', True),  # Hunter x Hunter (2011)
    21: ('원피스', True),  # One Piece
    19815: ('노 게임 노 라이프', True),  # No Game No Life
    11757: ('소드 아트 온라인', True),  # Sword Art Online
    21459: ('나의 히어로 아카데미아', True),  # Boku no Hero Academia
    20583: ('하이큐!!', True),  # Haikyuu!!
    30276: ('원펀맨', True),  # One Punch Man
    20954: ('이 멋진 세계에 축복을!', True),  # Kono Subarashii Sekai
    113415: ('주술회전', True),  # Jujutsu Kaisen
    16498: ('진격의 거인', True),  # Shingeki no Kyojin
    5114: ('강철의 연금술사 FULLMETAL ALCHEMIST', True),  # Fullmetal Alchemist: Brotherhood
    9253: ('스테인즈 게이트', True),  # Steins;Gate
    121: ('강철의 연금술사', True),  # Fullmetal Alchemist
    8074: ('히가시노 에덴', True),  # Higashi no Eden
    9919: ('CLANNAD ~AFTER STORY~', True),
    2904: ('CLANNAD', True),
    22199: ('도쿄구울', True),  # Tokyo Ghoul
    16664: ('노라가미', True),  # Noragami
    20974: ('노 게임 노 라이프 제로', True),  # No Game No Life: Zero
    33352: ('바이올렛 에버가든', True),  # Violet Evergarden
    32281: ('키즈나이버', True),  # Kiznaiver
    21939: ('올바른 카도', False),  # Seikaisuru Kado
    28223: ('산리오 남자', False),  # Sanrio Danshi
    30831: ('이 멋진 세계에 축복을! 2', True),  # KonoSuba 2
    102976: ('이 멋진 세계에 축복을! 극장판', True),  # KonoSuba Movie
    36474: ('이세계 스마트폰과 함께', True),  # Isekai wa Smartphone
    35839: ('뉴 게임!!', True),  # NEW GAME!!
    98292: ('우마 무스메 프리티 더비', True),  # Uma Musume
    103632: ('블루 피리어드', True),  # Blue Period
    136430: ('도쿄 리벤저스', True),  # Tokyo Revengers
    145064: ('도쿄 리벤저스: 성야결전편', True),  # Tokyo Revengers: Seiya Kessen-hen
    153288: ('도쿄 리벤저스: 천축편', True),  # Tokyo Revengers: Tenjiku-hen
    40748: ('던전에서 만남을 추구하면 안 되는 걸까 II', True),  # DanMachi II
    112323: ('던전에서 만남을 추구하면 안 되는 걸까 III', True),  # DanMachi III
    129874: ('던전에서 만남을 추구하면 안 되는 걸까 IV', True),  # DanMachi IV
    146065: ('던전에서 만남을 추구하면 안 되는 걸까 V', True),  # DanMachi V
    19221: ('니세코이', True),  # Nisekoi
    20031: ('니세코이:', True),  # Nisekoi:
    16417: ('역시 내 청춘 러브코메디는 잘못됐다', True),  # Yahari Ore
    23847: ('역시 내 청춘 러브코메디는 잘못됐다 속', True),  # Yahari Ore Zoku
    108489: ('역시 내 청춘 러브코메디는 잘못됐다 완', True),  # Yahari Ore Kan
    15583: ('데이트 어 라이브', True),  # Date A Live
    19163: ('데이트 어 라이브 II', True),  # Date A Live II
    100722: ('데이트 어 라이브 III', True),  # Date A Live III
    116605: ('데이트 어 라이브 IV', True),  # Date A Live IV
    157453: ('데이트 어 라이브 V', True),  # Date A Live V
    22789: ('베이비 스텝', True),  # Baby Steps
    20785: ('베이비 스텝 2', True),  # Baby Steps 2
    2167: ('CLANNAD 극장판', True),  # CLANNAD Movie
    22043: ('니세코이 OVA', True),  # Nisekoi OVA
    112641: ('극장판 바이올렛 에버가든', True),  # Violet Evergarden Movie
    10271: ('도라에몽 극장판: 노비타의 인어전설', False),  # Doraemon
    15417: ('도라에몽 극장판: 노비타와 기적의 섬', False),  # Doraemon
    18857: ('도라에몽 극장판: 노비타의 비밀도구 박물관', False),  # Doraemon
    22199: ('도쿄구울', True),  # Tokyo Ghoul
    22789: ('도쿄구울 √A', True),  # Tokyo Ghoul √A
}

def main():
    conn = sqlite3.connect('/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db')
    cursor = conn.cursor()

    print(f"\n총 {len(KOREAN_TITLES)}개 애니메이션 한국어 제목 업데이트 시작...\n")

    updated = 0
    skipped = 0

    for anime_id, (korean_title, is_official) in KOREAN_TITLES.items():
        cursor.execute("SELECT title_romaji FROM anime WHERE id = ?", (anime_id,))
        result = cursor.fetchone()

        if result:
            romaji_title = result[0]
            cursor.execute("""
                UPDATE anime
                SET title_korean = ?, title_korean_official = ?
                WHERE id = ?
            """, (korean_title, 1 if is_official else 0, anime_id))

            official_mark = "🔵" if is_official else "⚪"
            print(f"{official_mark} {anime_id}: {romaji_title} → {korean_title}")
            updated += 1
        else:
            print(f"⚠️  {anime_id}: 애니메이션을 찾을 수 없음")
            skipped += 1

    conn.commit()
    conn.close()

    print(f"\n" + "="*60)
    print(f"업데이트 완료!")
    print(f"="*60)
    print(f"  업데이트: {updated}개")
    print(f"  스킵: {skipped}개")
    print(f"="*60 + "\n")

if __name__ == '__main__':
    main()
