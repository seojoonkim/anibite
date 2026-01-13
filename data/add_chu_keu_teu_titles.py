"""
나무위키 ㅊ, ㅋ, ㅌ 초성 제목 추가
"""
import sqlite3
import re

DB_PATH = '/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db'

# 한국어 제목과 영어/로마자 키워드 매핑
TITLES = {
    # ㅊ 초성 (주요 작품)
    '창궁의 파프너': ['fafner', 'soukyuu no fafner'],
    '창성의 아쿠에리온': ['aquarion', 'sousei no aquarion'],
    '천공의 성 라퓨타': ['laputa', 'castle in the sky'],
    '천공의 에스카플로네': ['escaflowne'],
    '천원돌파 그렌라간': ['gurren lagann', 'tengen toppa'],
    '천체의 메소드': ['sora no method', 'celestial method'],
    '철완 아톰': ['astro boy', 'tetsuwan atom'],
    '철인 28호': ['tetsujin'],
    '첫 갸루': ['hajimete no gal'],
    '청의 엑소시스트': ['ao no exorcist', 'blue exorcist'],
    '청춘 돼지는 바니걸 선배의 꿈을 꾸지 않는다': ['seishun buta', 'bunny girl', 'aobuta'],
    '체인소 맨': ['chainsaw man'],
    '체포하겠어': ['you\'re under arrest', 'taiho shichauzo'],
    '초속 5센티미터': ['5 centimeters', 'byousoku 5'],
    '초시공요새 마크로스': ['macross'],
    '총몽': ['gunnm', 'battle angel'],
    '최애의 아이': ['oshi no ko'],
    '츠키모노가타리': ['tsukimonogatari'],
    '츠루네': ['tsurune'],
    '츠바사 크로니클': ['tsubasa chronicle'],
    '치하야후루': ['chihayafuru'],
    '침략! 오징어 소녀': ['shinryaku ika musume', 'squid girl'],

    # ㅋ 초성 (주요 작품)
    '카구야 님은 고백받고 싶어': ['kaguya', 'kokurasetai'],
    '카드캡터 사쿠라': ['cardcaptor sakura'],
    '카드캡터 사쿠라 클리어 카드 편': ['clear card'],
    '카레이도 스타': ['kaleido star'],
    '카우보이 비밥': ['cowboy bebop'],
    '카케구루이': ['kakegurui'],
    '칼 이야기': ['katanagatari'],
    '캠피오네!': ['campione'],
    '캐릭캐릭 체인지': ['shugo chara'],
    '캡틴 츠바사': ['captain tsubasa'],
    '케이온!': ['k-on'],
    '케모노 프렌즈': ['kemono friends'],
    '코드 기아스 반역의 를르슈': ['code geass'],
    '코드 기아스 반역의 를르슈 R2': ['code geass r2'],
    '코미 양은 커뮤증입니다': ['komi', 'komyushou'],
    '코바야시네 메이드래곤': ['maidragon', 'kobayashi'],
    '코코로 도서관': ['kokoro toshokan'],
    '코쿠리코 언덕에서': ['kokuriko', 'from up on poppy hill'],
    '쿠로코의 농구': ['kuroko', 'basket'],
    '크게 휘두르며': ['ookiku furikabutte', 'big windup'],
    '크레용 신짱': ['crayon shin', 'shinchan'],
    '클라나드': ['clannad'],
    '클레이모어': ['claymore'],
    '키노의 여행': ['kino no tabi', 'kino\'s journey'],
    '킬라킬': ['kill la kill'],
    '킹덤': ['kingdom'],
    '키즈모노가타리': ['kizumonogatari'],

    # ㅌ 초성 (주요 작품)
    '타나카 군은 항상 나른해': ['tanaka-kun', 'listless'],
    '타마코 마켓': ['tamako market'],
    '타마코 러브 스토리': ['tamako love story'],
    '타이거 마스크': ['tiger mask'],
    '탐정학원Q': ['tantei gakuen q'],
    '테니스의 왕자': ['prince of tennis', 'tenipuri'],
    '테라포마스': ['terraformars'],
    '테르마이 로마이': ['thermae romae'],
    '토라도라!': ['toradora'],
    '토리코': ['toriko'],
    '톱을 노려라!': ['gunbuster', 'top wo nerae'],
    '톱을 노려라2!': ['diebuster'],
    '투 러브 트러블': ['to love ru'],
    '투하트': ['to heart'],
    '트라이건': ['trigun'],
    '트루 티어즈': ['true tears'],
    '트리니티 블러드': ['trinity blood'],
    '트리니티 세븐': ['trinity seven'],
}

def normalize_text(text):
    """텍스트 정규화 (비교용)"""
    if not text:
        return ""
    # 소문자 변환 및 특수문자 제거
    normalized = text.lower()
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def match_title(korean_title, keywords, romaji, english):
    """
    키워드로 제목 매칭
    """
    romaji_norm = normalize_text(romaji) if romaji else ""
    english_norm = normalize_text(english) if english else ""

    for keyword in keywords:
        keyword_norm = normalize_text(keyword)
        if keyword_norm in romaji_norm or keyword_norm in english_norm:
            return True

    return False

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\nㅊ, ㅋ, ㅌ 초성 제목 {len(TITLES)}개 매칭 시작...\n")

    # 한국어 제목이 공식이 아닌 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english, title_korean
        FROM anime
        WHERE title_korean_official = 0
        ORDER BY popularity DESC
    """)

    anime_list = cursor.fetchall()

    updated = 0

    for korean_title, keywords in TITLES.items():
        matched = False

        for anime_id, romaji, english, current_korean in anime_list:
            if match_title(korean_title, keywords, romaji, english):
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
    print(f"ㅊ, ㅋ, ㅌ 초성 매칭 완료!")
    print(f"{'='*60}")
    print(f"  업데이트: {updated}개")
    print(f"  총 공식 제목: {total_official}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
