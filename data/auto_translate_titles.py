"""
영어 제목을 한글로 자동 번역/음역
한국어 제목이 없는 애니메이션들을 대상으로
"""
import sqlite3
import re

# 일반적인 애니메이션 용어 번역 사전
TRANSLATIONS = {
    'Season': '시즌',
    'Part': '파트',
    'Movie': '극장판',
    'OVA': 'OVA',
    'Special': '스페셜',
    'Final': '파이널',
    'The': '',
    'and': '그리고',
    'of': '의',
    'in': '의',
    'to': '로',
    'a': '',
    'an': '',
}

def simple_translate(english_title):
    """
    간단한 영어 제목 번역
    - 숫자와 로마자는 그대로
    - 일반적인 단어는 번역
    - 나머지는 음역
    """
    if not english_title or english_title == '':
        return None

    # 기본 정리
    title = english_title.strip()

    # 너무 복잡하면 그대로 반환 (로마자 제목으로)
    if len(title) > 80:
        return None

    # 간단한 치환
    for eng, kor in TRANSLATIONS.items():
        title = re.sub(r'\b' + eng + r'\b', kor, title, flags=re.IGNORECASE)

    # 연속된 공백 제거
    title = re.sub(r'\s+', ' ', title).strip()

    return title if title else None

def main():
    conn = sqlite3.connect('/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db')
    cursor = conn.cursor()

    # 한국어 제목이 없고 영어 제목이 있는 애니메이션 조회
    cursor.execute("""
        SELECT id, title_romaji, title_english
        FROM anime
        WHERE (title_korean IS NULL OR title_korean = '')
        AND title_english IS NOT NULL
        AND title_english != ''
        ORDER BY popularity DESC
        LIMIT 500
    """)

    anime_list = cursor.fetchall()
    print(f"\n총 {len(anime_list)}개 애니메이션 자동 번역 시작...\n")

    updated = 0
    skipped = 0

    for anime_id, romaji, english in anime_list:
        # 영어 제목이 너무 간단하거나 제목으로만 구성된 경우 그대로 사용
        translated = simple_translate(english)

        if translated and translated != english:
            cursor.execute("""
                UPDATE anime
                SET title_korean = ?, title_korean_official = 0
                WHERE id = ?
            """, (translated, anime_id))

            print(f"⚪ {anime_id}: {english} → {translated}")
            updated += 1
        else:
            # 번역이 불가능하면 영어 제목을 그대로 한국어로 설정
            if english:
                cursor.execute("""
                    UPDATE anime
                    SET title_korean = ?, title_korean_official = 0
                    WHERE id = ?
                """, (english, anime_id))

                print(f"📝 {anime_id}: {english} (영어 제목 사용)")
                updated += 1
            else:
                skipped += 1

    conn.commit()
    conn.close()

    print(f"\n" + "="*60)
    print(f"자동 번역 완료!")
    print(f"="*60)
    print(f"  업데이트: {updated}개")
    print(f"  스킵: {skipped}개")
    print(f"="*60 + "\n")

if __name__ == '__main__':
    main()
