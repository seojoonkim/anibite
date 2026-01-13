"""
스태프 데이터 크롤링
상위 3,000개 애니메이션의 제작진 정보 수집 (감독, 각본가, 프로듀서 등)
"""
import os
import sys

from crawler import AnimeCrawler

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   👔 스태프 데이터 크롤링                                  ║
║   대상: 상위 3,000개 애니메이션                           ║
╚════════════════════════════════════════════════════════════╝
    """)

    crawler = AnimeCrawler()
    crawler.connect()

    try:
        # 이미 애니메이션 데이터가 있는 것들에 대해 스태프 추가
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
                # 스태프 데이터 가져오기
                response = crawler.client.get_anime_staff(anime_id)

                if response and 'Media' in response:
                    anime_data = response['Media']
                    # 스태프 저장
                    staff_edges = anime_data.get('staff', {}).get('edges', [])
                    staff_count = 0
                    for staff_edge in staff_edges:
                        staff_node = staff_edge.get('node')
                        if staff_node:
                            staff_id = staff_node.get('id')
                            role = staff_edge.get('role')

                            if staff_id and staff_id not in crawler.existing_staff_ids:
                                # 스태프 테이블에 저장
                                occupations = staff_node.get('primaryOccupations', [])
                                occupations_str = ','.join(occupations) if occupations else None

                                crawler.conn.execute("""
                                    INSERT OR IGNORE INTO staff (
                                        id, name_full, name_native,
                                        language, image_url,
                                        description, favourites,
                                        primary_occupations
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    staff_id,
                                    staff_node.get('name', {}).get('full'),
                                    staff_node.get('name', {}).get('native'),
                                    staff_node.get('languageV2'),
                                    staff_node.get('image', {}).get('large'),
                                    staff_node.get('description'),
                                    staff_node.get('favourites'),
                                    occupations_str
                                ))
                                crawler.existing_staff_ids.add(staff_id)

                            # 애니메이션-스태프 관계 저장
                            if staff_id and role:
                                crawler.conn.execute("""
                                    INSERT OR IGNORE INTO anime_staff (
                                        anime_id, staff_id, role
                                    ) VALUES (?, ?, ?)
                                """, (anime_id, staff_id, role))

                            staff_count += 1

                    crawler.conn.commit()
                    success_count += 1
                    print(f"  ✅ 스태프 {staff_count}명 저장")

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
