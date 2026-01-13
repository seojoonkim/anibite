"""
한국어 제목 배치 업데이트 (2차)
인기 애니메이션 추가분
"""
import sqlite3

# 한국어 제목 매핑 (anime_id: (korean_title, is_official))
KOREAN_TITLES = {
    # 이미 업데이트한 4개
    20626: ('페어리 테일', True),
    114963: ('울고 싶은 나는 고양이 가면을 쓴다', True),
    97994: ('블렌드 S', True),
    142770: ('스즈메의 문단속', True),

    # 추가 인기 애니메이션
    2890: ('벼랑 위의 포뇨', True),  # Gake no Ue no Ponyo
    512: ('마녀 배달부 키키', True),  # Majo no Takkyuubin
    21701: ('쓰레기의 본망', True),  # Kuzu no Honkai
    18671: ('중2병이라도 사랑이 하고 싶어! 연', True),  # Chuunibyou demo Koi ga Shitai! Ren
    154965: ('야마다 군과 Lv999의 사랑을 한다', True),  # Yamada-kun to Lv999 no Koi wo Suru
    2966: ('늑대와 향신료', True),  # Ookami to Koushinryou
    131942: ('죠죠의 기묘한 모험 스톤 오션', True),  # JoJo's Bizarre Adventure: Stone Ocean
    16894: ('쿠로코의 농구 2기', True),  # Kuroko no Basket 2nd SEASON
    131586: ('86 에이티식스 Part 2', True),  # 86: Eighty Six Part 2
    178025: ('가치악타', True),  # Gachiakuta
    21861: ('청의 엑소시스트 교토 부정왕편', True),  # Ao no Exorcist: Kyoto Fujouou-hen
    777: ('헬싱 OVA', True),  # HELLSING OVA
    21058: ('빨강머리 백설공주', True),  # Akagami no Shirayuki-hime
    21428: ('회색도시 그림가르', True),  # Hai to Gensou no Grimgar
    934: ('쓰르라미 울 적에', True),  # Higurashi no Naku Koro ni
    128546: ('Vivy: Fluorite Eye\'s Song', True),  # Vivy
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

            print(f"✅ {anime_id}: {romaji_title} → {korean_title}")
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
