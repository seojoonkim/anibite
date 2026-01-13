"""
캐릭터 & 성우 데이터 크롤링
상위 3,000개 애니메이션의 캐릭터와 성우 정보 수집
"""
import os
import sys

from crawler import AnimeCrawler

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   👥 캐릭터 & 성우 데이터 크롤링                          ║
║   대상: 상위 3,000개 애니메이션                           ║
╚════════════════════════════════════════════════════════════╝
    """)

    crawler = AnimeCrawler()
    crawler.connect()

    try:
        # 이미 애니메이션 데이터가 있는 것들에 대해 캐릭터/성우 추가
        cursor = crawler.conn.cursor()
        cursor.execute("""
            SELECT id, title_romaji
            FROM anime
            ORDER BY popularity DESC
            LIMIT 3000
        """)

        anime_list = cursor.fetchall()
        total = len(anime_list)

        print(f"📊 크롤링 대상: {total}개 애니메이션\n")

        success_count = 0
        error_count = 0

        for i, (anime_id, title) in enumerate(anime_list, 1):
            print(f"\n[{i}/{total}] {title} (ID: {anime_id})")

            try:
                # 캐릭터 & 성우 데이터 가져오기
                response = crawler.client.get_anime_characters(anime_id)

                if response and 'Media' in response:
                    anime_data = response['Media']
                    # 캐릭터 저장
                    characters = anime_data.get('characters', {}).get('edges', [])
                    char_count = 0
                    for char_edge in characters[:25]:  # 상위 25명
                        char_node = char_edge.get('node')
                        if char_node:
                            char_id = char_node.get('id')
                            if char_id and char_id not in crawler.existing_char_ids:
                                # 캐릭터 저장
                                crawler.conn.execute("""
                                    INSERT OR IGNORE INTO character (
                                        id, name_full, name_native,
                                        image_url, description, favourites
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    char_id,
                                    char_node.get('name', {}).get('full'),
                                    char_node.get('name', {}).get('native'),
                                    char_node.get('image', {}).get('large'),
                                    char_node.get('description'),
                                    char_node.get('favourites')
                                ))
                                crawler.existing_char_ids.add(char_id)

                            # 애니메이션-캐릭터 관계 저장
                            role = char_edge.get('role', 'SUPPORTING')
                            crawler.conn.execute("""
                                INSERT OR IGNORE INTO anime_character (
                                    anime_id, character_id, role
                                ) VALUES (?, ?, ?)
                            """, (anime_id, char_id, role))

                            # 성우 정보 (이미 API에서 Japanese로 필터링됨)
                            voice_actors = char_edge.get('voiceActors', [])
                            for va in voice_actors:
                                va_id = va.get('id')
                                if va_id:
                                    # 스태프 테이블에 저장
                                    if va_id not in crawler.existing_staff_ids:
                                        crawler.conn.execute("""
                                            INSERT OR IGNORE INTO staff (
                                                id, name_full, name_native,
                                                language, image_url,
                                                description, favourites,
                                                primary_occupations
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            va_id,
                                            va.get('name', {}).get('full'),
                                            va.get('name', {}).get('native'),
                                            va.get('language', 'Japanese'),
                                            va.get('image', {}).get('large'),
                                            va.get('description'),
                                            va.get('favourites'),
                                            None
                                        ))
                                        crawler.existing_staff_ids.add(va_id)

                                    # 캐릭터-성우 관계 저장
                                    crawler.conn.execute("""
                                        INSERT OR IGNORE INTO character_voice_actor (
                                            character_id, staff_id, anime_id, language
                                        ) VALUES (?, ?, ?, ?)
                                    """, (char_id, va_id, anime_id, 'Japanese'))

                            char_count += 1

                    crawler.conn.commit()
                    success_count += 1
                    print(f"  ✅ 캐릭터 {char_count}명 저장")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                error_count += 1
                print(f"  ❌ 에러: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✅ 크롤링 완료!")
        print(f"{'='*60}")
        print(f"  성공: {success_count}개")
        print(f"  실패: {error_count}개")
        print(f"{'='*60}\n")

    finally:
        crawler.close()

if __name__ == '__main__':
    import time
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨")
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
