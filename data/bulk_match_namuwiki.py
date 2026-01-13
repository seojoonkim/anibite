"""
나무위키 대량 제목 매칭
수백 개의 한국어 제목을 데이터베이스와 자동 매칭
"""
import sqlite3
import re

# 나무위키에서 수집한 모든 한국어 제목들
NAMU_TITLES = [
    # ㅂ 초성 (212개)
    '바나나 피쉬', '바니타스의 수기', '바다가 들린다', '바다의 무녀', '바라카몬',
    '바람계곡의 나우시카', '바람의 검심', '바이올렛 에버가든', '바질리스크',
    '바카노!', '바쿠만', '반딧불의 묘', '반딧불이의 숲으로', '반요 야샤히메',
    '방패 용사의 성공담', '배가본드', '배신자는 내 이름을 알고 있다', '배틀로얄',
    '백곰 카페', '백성귀족', '백성녀와 흑목사', '백작과 요정', '뱀부 블레이드',
    '뱀파이어 기사', '뱀파이어 헌터', '벚꽃사중주', '벼랑 위의 포뇨',
    '변태왕자와 웃지 않는 고양이', '별을 쫓는 아이', '별의 목소리', '별의 커비',
    '베르사이유의 장미', '베르세르크', '베이비 스텝', '벨제바브', '보루토',
    '보석의 나라', '보노보노', '봉신연의', '부기팝은 웃지 않는다', '북두의 권',
    '북으로', '불꽃소년 레카', '불꽃의 미라주', '불꽃의 전학생', '불새',
    '불멸의 그대에게', '붓다', '붉은 돼지', '브레이브 스토리', '브레인 파워드',
    '블랙 라군', '블랙 불릿', '블랙 잭', '블랙캣', '블렌드 S', '블러드 래드',
    '블러드C', '블레이드', '블레이드 앤 소울', '블루 드롭', '블루 젠더',
    '블루 록', '블루 피리어드', '블리치', '블랙 클로버', '비색의 조각',
    '비탄의 아리아', '빅 오더', '빈곤자매 이야기', '빈란드 사가', '빙과',
    '빨간망토 차차', '빨강머리 백설공주', '빨강머리 앤',

    # ㅅ 초성 (111개)
    '사랑과 거짓말', '사랑과 선거와 초콜릿', '사랑은 비가 갠 뒤처럼',
    '사무라이 7', '사무라이 참프루', '사무라이 플라멩코', '사무라이건',
    '사상최강의 제자 켄이치', '사이보그 009', 'PSYCHO-PASS', '사이키 쿠스오의 재난',
    '사자에상', '사카모토입니다만?', '사키', '사쿠라 대전', '사쿠라 퀘스트',
    '사쿠라 트릭', '사쿠라다 리셋', '사쿠라장의 애완 그녀', '산카레아',
    '살육의 천사', '삼자삼엽', '새벽의 연화', '샤먼킹', '샤를로트', '샹그리라',
    '섀도 하우스', '서번트×서비스', '선계전 봉신연의', '선녀전설 세레스',
    '섬광의 나이트레이드', '섬란 카구라', '성검사의 금주영창', '성검의 블랙스미스',
    '성흔의 퀘이사', '세기말 오컬트 학원', '세계에서 제일 강해지고 싶어!',
    '세계정복', '세라핌 콜', '세이렌', '세인트 세이야', '세인트 영멘',
    '세일러복과 중전차', '세킬레이', '세토의 신부', '셜록', '소년탐정 김전일',
    '소드 아트 온라인', '소드걸즈', '소라의 날개', '소녀는 언니를 사랑해',
    '소녀☆가극 레뷰 스타라이트', '소울 이터', '소울워커', '손가락 아저씨',
    '손 전재', '송곳니', '쇼군왕', '슈퍼 큐브', '스레이어즈', '스즈미야 하루히',
    '스켓댄스', '스쿨럼블', '스크라이드', '스크립트 코드', '스타 오션',
    '스타워너비', '스타트윙클 프리큐어', '스타☆트윈클 프리큐어', '스탠드 마이 히어로즈',
    '스트라이크 더 블러드', '스트라이크 위치스', '스트레인저: 무황인담',
    '스트리트 파이터', '스틸볼 런', '시고후미', '시귀', '시끌별 녀석들',
    '시도니아의 기사', '시몬', '시원찮은 그녀를 위한 육성방법', '시티헌터',
    '신세계에서', '신세기 GPX 사이버 포뮬러', '신세기 에반게리온', '신조',

    # ㄴ 초성 (90개)
    '나가토 유키짱의 소실', '나나', '나나마루 산바츠', '나는 친구가 적다',
    '나루타루', '나루토', '나만이 없는 거리', '나이츠 & 매직', '나이트 위저드',
    '나의 지구를 지켜줘', '나의 행복한 결혼', '나의 히어로 아카데미아',
    '나츠메 우인장', '낙원추방', '낙제 기사의 영웅담', '낚시왕 강바다',
    '난바카', '날씨의 아이', '날아라 호빵맨', '남자 고교생의 일상',
    '내가 인기 없는 건 아무리 생각해도 너희들 탓이야!', '내 뇌 속의 선택지',
    '내 여동생이 이렇게 귀여울 리가 없어', '내 이야기!!', '내일의 나쟈',
    '내일의 요이치!', '내일의 죠', '너에게 닿기를', '너와 나', '너의 이름은.',
    '너의 췌장을 먹고 싶어', '네코모노가타리', '네코파라', '노 게임 노 라이프',
    '노기자카 하루카의 비밀', '노다메 칸타빌레', '노라가미', '노래의☆왕자님♪',
    '노부나가 더 풀', '노블레스', '노에인', '노을빛으로 물드는 언덕', '논논비요리',
    '농림', '누라리횬의 손자', '눈의 여왕', '늑대아이', '늑대와 향신료',
    '늑대소녀와 흑왕자', '니들리스', '니세코이', '니세모노가타리', '닌자보이 란타로',

    # 이미 추가된 것들 (중복 포함)
    '가정교사 히트맨 REBORN!', '간츠', '갑철성의 카바네리', '건슬링거 걸',
    '귀멸의 칼날', '공각기동대', '기동전사 건담', '나나', '노다메 칸타빌레',
    '디지몬 어드벤처', '도라에몽', '도로로', '도쿄 구울', '도쿄 리벤저스',
    '란마 1/2', '러브히나', '로젠 메이든', '루팡 3세', '리라이프', '리틀 버스터즈!',
    '명탐정 코난', '모노노케 히메', '마법기사 레이어스', '마법선생 네기마!',
    '모브사이코 100', '마기', '하울의 움직이는 성', '하야테처럼!', '흑집사',
    '헤타리아', '혈계전선', '허니와 클로버', '학생회의 일존', '학원묵시록',
    '호오즈키의 냉철', '포켓몬스터', '풀 메탈 패닉', '프리큐어',
    '플라스틱 메모리즈', '펀치라인', '펌프킨 시저스', '페르소나', '표류교실',
    '푸른 강철의 아르페지오', '벼랑 위의 포뇨', '이웃집 토토로',
    '센과 치히로의 행방불명', '마녀 배달부 키키', '붉은 돼지',
]

def normalize_for_matching(text):
    """매칭을 위한 텍스트 정규화"""
    if not text:
        return ''
    # 소문자로 변환하고 특수문자 제거
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_keywords_from_korean(korean_title):
    """한국어 제목에서 영어 키워드 추출 (일반적인 변환)"""
    # 간단한 매핑
    mappings = {
        '바나나 피쉬': ['banana fish'],
        '바니타스': ['vanitas'],
        '바다가 들린다': ['ocean waves', 'umi ga kikoeru'],
        '바라카몬': ['barakamon'],
        '바람계곡의 나우시카': ['nausicaa', 'naushika', 'kaze no tani'],
        '바람의 검심': ['rurouni kenshin', 'kenshin', 'samurai x'],
        '바이올렛 에버가든': ['violet evergarden'],
        '바질리스크': ['basilisk'],
        '바카노': ['baccano'],
        '바쿠만': ['bakuman'],
        '반딧불의 묘': ['grave fireflies', 'hotaru no haka'],
        '반딧불이의 숲으로': ['hotarubi no mori'],
        '반요 야샤히메': ['yashahime', 'hanyo'],
        '방패 용사': ['tate no yuusha', 'shield hero'],
        '배가본드': ['vagabond'],
        '배신자는 내 이름을': ['uragiri', 'betrayal'],
        '백곰 카페': ['shirokuma', 'polar bear'],
        '백작과 요정': ['hakushaku', 'earl fairy'],
        '뱀부 블레이드': ['bamboo blade'],
        '뱀파이어 기사': ['vampire knight'],
        '벚꽃사중주': ['sakura', 'quartet'],
        '별을 쫓는 아이': ['hoshi wo ou', 'children who chase'],
        '별의 목소리': ['hoshi no koe', 'voices distant star'],
        '별의 커비': ['kirby', 'hoshi no kirby'],
        '베르사이유의 장미': ['rose of versailles', 'berusaiyu'],
        '베르세르크': ['berserk'],
        '베이비 스텝': ['baby steps'],
        '벨제바브': ['beelzebub'],
        '보루토': ['boruto'],
        '보석의 나라': ['houseki no kuni', 'land lustrous'],
        '보노보노': ['bonobono'],
        '봉신연의': ['houshin engi', 'feng shen'],
        '부기팝': ['boogiepop'],
        '북두의 권': ['hokuto no ken', 'fist north star'],
        '북으로': ['kita', 'north'],
        '불꽃소년 레카': ['rekka', 'flame recca'],
        '불꽃의 미라주': ['mirage'],
        '불새': ['hi no tori', 'phoenix'],
        '불멸의 그대에게': ['fumetsu', 'your eternity'],
        '붓다': ['buddha'],
        '블랙 라군': ['black lagoon'],
        '블랙 불릿': ['black bullet'],
        '블랙 잭': ['black jack'],
        '블랙캣': ['black cat'],
        '블러드 래드': ['blood lad'],
        '블러드C': ['blood c'],
        '블레이드': ['blade'],
        '블레이드 앤 소울': ['blade soul'],
        '블루 드롭': ['blue drop'],
        '블루 젠더': ['blue gender'],
        '블루 록': ['blue lock'],
        '블루 피리어드': ['blue period'],
        '블리치': ['bleach'],
        '블랙 클로버': ['black clover'],
        '비탄의 아리아': ['aria scarlet', 'hidan no aria'],
        '빅 오더': ['big order'],
        '빈곤자매': ['binbou shimai'],
        '빈란드 사가': ['vinland saga'],
        '빙과': ['hyouka'],
        '빨간망토 차차': ['akazukin chacha'],
        # ㅅ 초성
        '사랑과 거짓말': ['koi to uso', 'love lies'],
        '사랑과 선거와 초콜릿': ['koi to senkyo', 'love election chocolate'],
        '사랑은 비가 갠 뒤처럼': ['koi wa ameagari', 'after rain'],
        '사무라이 7': ['samurai 7', 'samurai seven'],
        '사무라이 참프루': ['samurai champloo'],
        '사무라이 플라멩코': ['samurai flamenco'],
        '사상최강의 제자 켄이치': ['kenichi', 'shijou saikyou'],
        '사이보그 009': ['cyborg 009'],
        'PSYCHO-PASS': ['psycho pass', 'psychopass'],
        '사이키 쿠스오': ['saiki kusuo', 'disastrous life'],
        '사자에상': ['sazae san'],
        '사카모토입니다만': ['sakamoto desu ga', 'havent you heard'],
        '사키': ['saki'],
        '사쿠라 대전': ['sakura taisen', 'sakura wars'],
        '사쿠라 퀘스트': ['sakura quest'],
        '사쿠라 트릭': ['sakura trick'],
        '사쿠라다 리셋': ['sakurada reset'],
        '사쿠라장의 애완 그녀': ['sakurasou', 'pet girl'],
        '산카레아': ['sankarea'],
        '살육의 천사': ['satsuriku no tenshi', 'angels of death'],
        '삼자삼엽': ['sansha sanyou'],
        '새벽의 연화': ['akatsuki no yona', 'yona dawn'],
        '샤먼킹': ['shaman king'],
        '샤를로트': ['charlotte'],
        '샹그리라': ['shangri la'],
        '섀도 하우스': ['shadow house', 'shadows house'],
        '서번트×서비스': ['servant service'],
        '선녀전설 세레스': ['ayashi no ceres', 'ceres celestial'],
        '섬광의 나이트레이드': ['senkou no night raid'],
        '섬란 카구라': ['senran kagura'],
        '성검사의 금주영창': ['seiken tsukai', 'world break'],
        '세기말 오컬트 학원': ['occult academy'],
        '세계정복': ['sekai seifuku'],
        '세이렌': ['seiren'],
        '세인트 세이야': ['saint seiya'],
        '세일러복과 중전차': ['girls und panzer'],
        '세킬레이': ['sekirei'],
        '세토의 신부': ['seto no hanayome', 'my bride mermaid'],
        # ㄴ 초성
        '나가토 유키짱의 소실': ['nagato yuki', 'disappearance'],
        '나나마루 산바츠': ['nana maru san batsu'],
        '나루타루': ['narutaru'],
        '나만이 없는 거리': ['boku dake ga inai machi', 'erased'],
        '나이츠 & 매직': ['knights magic'],
        '나의 지구를 지켜줘': ['boku earth', 'please save'],
        '낙원추방': ['rakuen tsuihou', 'expelled paradise'],
        '낙제 기사': ['rakudai kishi', 'chivalry failed knight'],
        '낚시왕 강바다': ['tsuri', 'fishing'],
        '난바카': ['nanbaka'],
        '날씨의 아이': ['tenki no ko', 'weathering with you'],
        '날아라 호빵맨': ['anpanman'],
        '남자 고교생의 일상': ['danshi koukousei', 'daily lives'],
        '내 뇌 속의 선택지': ['noucome', 'my mental choices'],
        '내일의 나쟈': ['ashita no nadja'],
        '내일의 요이치': ['samurai harem'],
        '내일의 죠': ['ashita no joe'],
        '너에게 닿기를': ['kimi ni todoke', 'reaching you'],
        '너와 나': ['kimi to boku'],
        '너의 이름은': ['kimi no na wa', 'your name'],
        '너의 췌장을': ['kimi no suizou', 'want eat pancreas'],
        '네코파라': ['nekopara'],
        '노기자카 하루카': ['nogizaka haruka'],
        '노래의☆왕자님': ['uta no prince', 'utapri'],
        '노부나가 더 풀': ['nobunaga fool'],
        '노블레스': ['noblesse'],
        '노에인': ['noein'],
        '노을빛으로 물드는 언덕': ['akane iro', 'akane mellow'],
        '농림': ['nourin', 'no rin'],
        '누라리횬의 손자': ['nurarihyon no mago'],
        '눈의 여왕': ['snow queen'],
        '늑대아이': ['ookami kodomo', 'wolf children'],
        '늑대소녀와 흑왕자': ['ookami shoujo', 'wolf girl black prince'],
        '니들리스': ['needless'],
    }

    title_lower = korean_title.lower().strip()
    if title_lower in mappings:
        return mappings[title_lower]

    # 기본적으로 제목 자체를 키워드로 사용
    return [normalize_for_matching(korean_title)]

def main():
    conn = sqlite3.connect('/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db')
    cursor = conn.cursor()

    # 중복 제거
    unique_titles = list(set(NAMU_TITLES))
    print(f"\n나무위키 제목 {len(unique_titles)}개 매칭 시작...\n")

    # 데이터베이스에서 공식 제목이 아닌 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english, title_korean
        FROM anime
        WHERE title_korean_official = 0
        ORDER BY popularity DESC
    """)

    anime_list = cursor.fetchall()

    updated = 0
    matched_titles = set()

    for korean_title in unique_titles:
        if korean_title in matched_titles:
            continue

        keywords = get_keywords_from_korean(korean_title)

        for anime_id, romaji, english, current_korean in anime_list:
            romaji_norm = normalize_for_matching(romaji or '')
            english_norm = normalize_for_matching(english or '')

            # 키워드 매칭
            found = False
            for keyword in keywords:
                keyword_norm = normalize_for_matching(keyword)
                if keyword_norm and (keyword_norm in romaji_norm or keyword_norm in english_norm):
                    found = True
                    break

            if found:
                # 업데이트
                cursor.execute("""
                    UPDATE anime
                    SET title_korean = ?, title_korean_official = 1
                    WHERE id = ?
                """, (korean_title, anime_id))

                print(f"🔵 {anime_id}: {romaji or english} → {korean_title}")
                updated += 1
                matched_titles.add(korean_title)
                break

    conn.commit()

    # 현재 공식 제목 총 개수 확인
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
    total_official = cursor.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"나무위키 대량 매칭 완료!")
    print(f"{'='*60}")
    print(f"  업데이트: {updated}개")
    print(f"  총 공식 제목: {total_official}개")
    print(f"  초기 대비: +{total_official - 589}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
