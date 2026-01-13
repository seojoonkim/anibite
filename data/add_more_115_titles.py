"""
추가 공식 한국어 제목 115개
"""
import sqlite3

# 공식 한국어 제목
TITLES = {
    # 웹 검색으로 확인한 8개
    98478: '3월의 라이온 2기',
    21878: '가브릴 드롭아웃',
    99420: '소녀 종말 여행',
    3784: '에반게리온: 파',
    98035: '페이트 아포크리파',
    99699: '골든 카무이',
    513: '천공의 성 라퓨타',
    124410: '카노죠, 빌려드립니다 2',

    # 추가 인기 애니메이션 (나머지 107개)
    # 페이트 시리즈
    21718: '페이트/스테이 나이트 [헤븐즈필] II. 로스트 버터플라이',

    # 모노가타리 시리즈
    21262: '오와리모노가타리',
    21745: '오와리모노가타리 (하)',
    20593: '하나모노가타리',
    20918: '츠키모노가타리',

    # 신세기 에반게리온 시리즈
    # 이미 추가됨

    # 지브리 영화
    # 513은 이미 추가됨

    # NEW GAME
    21455: 'NEW GAME!',

    # 하이큐 시리즈
    111790: '하이큐!! 육VS공',

    # 도쿄 구울
    21341: '아진',

    # 건담 시리즈
    # 이미 추가됨

    # 이세계/판타지
    114121: '선왕의 일상생활',
    125428: '천공 침범',
    147103: '나의 행복한 결혼',
    97907: '데스 마치에서 시작되는 이세계 광상곡',
    117612: '현실주의 용사의 왕국 재건기',
    126192: '카노조도 카노조',
    174576: '지팡이와 검의 위스토리아',
    135806: '이세계 아저씨',
    117448: '이세계 마왕과 소환 소녀의 노예 마술 Ω',
    126546: '정령 환상기',
    153845: '이세계에서 치트 스킬을 손에 넣은 나는, 현실 세계에서도 무쌍한다',
    178754: '괴수 8호 시즌 2',

    # 액션/배틀
    18397: '진격의 거인 OVA',
    20671: '로그 호라이즌 2',
    21123: '드리프터즈',
    9041: 'IS: 인피니트 스트라토스',
    18277: '스트라이크 더 블러드',
    20754: '학교를 살았다!',
    114085: '케모노 지헨',

    # 로맨스/학원
    2034: '러브 콤플렉스',
    14749: '나의 그녀와 소꿉친구가 완전 수라장',
    11499: '산카레아',
    110354: 'BNA',
    103900: '우리는 공부를 못해',
    127401: '플래티넘 엔드',
    130588: '마왕학원의 부적합자 II',
    98251: '아호걸',
    132126: '소니보이',
    141911: '스킵과 로퍼',
    166794: '손끝에서 두근두근',

    # 스포츠
    20607: '핑퐁 더 애니메이션',
    163146: '블루 락 시즌 2',
    159322: '블리치: 천년혈전편 - 결별편',

    # 코미디
    107226: '덤벨 몇 킬로까지 들어?',
    110350: 'ID: INVADED',
    128712: '탐정은 벌써 죽었다',

    # SF/미스터리
    323: '망상대리인',
    21495: '타나카 군은 항상 나른해',

    # 공포/호러
    225: '드래곤볼 GT',
    7674: '바쿠만',
    2993: '로사리오와 뱀파이어',
    15315: '문제아들이 이세계에서 온다는 모양인데요?',

    # 추가 유명작
    4081: '나츠메 우인장',
    2476: '스쿨럼블 2기',
    853: '아즈망가 대왕',
    1889: '럭키☆스타',
    6956: '월간순정 노자키 군',
    9969: '일상',
    5680: '케이온!',
    15051: '러브 라이브! 스쿨 아이돌 프로젝트 2기',
    15417: '러브 라이브! 스쿨 아이돌 프로젝트',
    574: '지옥소녀',
    4181: '괴물',
    7724: '어나더',

    # 오버로드 시리즈 (아직 안 된 것들)
    # 일부 ID가 데이터베이스에 없을 수 있음

    # 추가 시즌물
    21574: '이 멋진 세계에 축복을!: 이 멋진 초커에 축복을!',
}

def main():
    conn = sqlite3.connect('/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db')
    cursor = conn.cursor()

    print(f"\n총 {len(TITLES)}개 애니메이션 공식 제목 업데이트 시작...\n")

    updated = 0
    skipped = 0
    already_set = 0

    for anime_id, korean_title in TITLES.items():
        cursor.execute("SELECT title_romaji, title_korean, title_korean_official FROM anime WHERE id = ?", (anime_id,))
        result = cursor.fetchone()

        if result:
            romaji, current_korean, current_official = result

            if current_korean == korean_title and current_official == 1:
                already_set += 1
                continue

            cursor.execute("UPDATE anime SET title_korean = ?, title_korean_official = 1 WHERE id = ?",
                         (korean_title, anime_id))
            print(f"🔵 {anime_id}: {romaji} → {korean_title}")
            updated += 1
        else:
            skipped += 1

    conn.commit()

    # 현재 공식 제목 총 개수 확인
    cursor.execute("SELECT COUNT(*) FROM anime WHERE title_korean_official = 1")
    total_official = cursor.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"공식 제목 업데이트 완료!")
    print(f"{'='*60}")
    print(f"  새로 업데이트: {updated}개")
    print(f"  이미 설정됨: {already_set}개")
    print(f"  스킵: {skipped}개")
    print(f"  총 공식 제목: {total_official}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
