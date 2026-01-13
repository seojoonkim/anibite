"""
마지막 55개 공식 한국어 제목
"""
import sqlite3

TITLES = {
    # 키즈모노가타리 시리즈
    9260: '키즈모노가타리 I: 철혈편',
    21399: '키즈모노가타리 II: 열혈편',

    # Fate 시리즈
    20791: '페이트/스테이 나이트 [헤븐즈필] I. 프레자지 플라워',

    # 에반게리온 시리즈
    2759: '에반게리온: 서',
    3785: '에반게리온: 큐',

    # 인기 애니메이션
    113425: '회복술사의 재시작',
    115113: '우자키짱은 놀고 싶어!',
    104647: '악역 영애에게는 파멸 플래그만이...',
    178788: '귀멸의 칼날: 무한성편 영화 1 - 아카자 재래',
    17729: '그리자이아의 과실',
    163132: '호리미야: 피스',
    97832: '시트러스',
    1887: '럭키☆스타',
    99457: '작별의 아침에 약속의 꽃을 장식하자',
    114194: '비스타스 2기',
    109190: '바이올렛 에버가든 외전: 영원과 자동 수기 인형',
    20513: '사이코패스 2',
    97863: '첫 갸루',
    100298: '메갈로 박스',
    99749: '페어리 테일 (2018)',
    11633: '블러드 래드',
    16870: 'THE LAST: 나루토 더 무비',
    143338: '옆집 천사님께서 어느새 나를 무능력자로 만들어버렸다',
    16067: '나기의 아스카라',
    153152: '나의 마음의 위험한 녀석',
    11577: '스테인즈 게이트: 부하 영역의 데자뷔',
    111322: '방패 용사의 성공담 시즌 3',
    270: '헬싱',
    3455: 'To LOVE-Ru 투 러브 트러블',
    21306: '무채한의 팬텀 월드',
    21290: '넷게임의 신부는 여자애가 아니라고 생각했나?',
    142853: '도쿄 리벤저스: 성야결전편',
    112443: '약캐릭터 토모자키 군',
    141949: '부부 이상, 연인 미만',
    104464: '나를 좋아하는 건 너뿐이냐',
    6594: '칼 이야기',
    116752: '일곱 개의 대죄: 분노의 심판',
    101573: '이윽고 너에게 닿을',
    20773: '갱스타',
    97980: 'Re: CREATORS',
    151384: '카구야 님은 고백받고 싶어: 퍼스트 키스는 끝나지 않아',
    263: '첫걸음: THE FIGHTING!',
    99726: '넷게임 폐인의 추천',
    8525: '신만이 아는 세계',
    153800: '원펀맨 3',
    97767: '하이스쿨 D×D HERO',
    112608: '슬라임을 쓰러뜨린지 300년, 모르는 사이에 레벨 MAX가 되었습니다',
    20955: '육화의 용사',
    11759: '액셀 월드',
    97888: '바키',
    101168: '플런더러',
    21364: '게이트: 자위대. 그곳에서, 이렇게 싸웠다 Part 2',
    17549: '논논비요리',
    137281: '아하렌 씨는 재지 않아',
    170942: '파란 상자',
    21499: '쌍성의 음양사',
    8425: '고식',
    162670: '닥터 스톤: NEW WORLD Part 2',
    118375: '나만 들어갈 수 있는 숨은 던전',
    154116: '언데드 언럭',
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
    print(f"  초기 대비: +{total_official - 384}개")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
