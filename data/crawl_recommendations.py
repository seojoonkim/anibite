"""
추천 데이터 크롤링
애니메이션 간의 추천 관계 수집 (비슷한 작품)
"""
import os
import sys

from crawler import AnimeCrawler

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   💡 추천 데이터 크롤링                                    ║
║   대상: 상위 3,000개 애니메이션                           ║
╚════════════════════════════════════════════════════════════╝
    """)

    crawler = AnimeCrawler()
    crawler.connect()

    try:
        # 이미 애니메이션 데이터가 있는 것들에 대해 추천 추가
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
        total_recommendations = 0

        for i, (anime_id, title) in enumerate(anime_list, 1):
            print(f"\n[{i}/{total}] {title} (ID: {anime_id})")

            try:
                # 추천 데이터 가져오기 (일반 get_popular_anime_page 쿼리에 포함되어 있음)
                # AniList API에서 recommendations를 가져오는 별도 쿼리 필요
                query = """
                query ($id: Int) {
                    Media(id: $id) {
                        recommendations(sort: RATING_DESC) {
                            edges {
                                node {
                                    rating
                                    mediaRecommendation {
                                        id
                                        title {
                                            romaji
                                            english
                                            native
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """

                variables = {'id': anime_id}
                response = crawler.client._make_request(query, variables)

                if response and 'Media' in response:
                    recommendations = response['Media'].get('recommendations', {}).get('edges', [])
                    rec_count = 0

                    for rec_edge in recommendations[:10]:  # 상위 10개 추천만
                        rec_node = rec_edge.get('node')
                        if rec_node:
                            rating = rec_node.get('rating', 0)
                            recommended_media = rec_node.get('mediaRecommendation')

                            if recommended_media:
                                recommended_id = recommended_media.get('id')

                                if recommended_id:
                                    # 추천 관계 저장
                                    crawler.conn.execute("""
                                        INSERT OR IGNORE INTO anime_recommendation (
                                            anime_id, recommended_anime_id, rating
                                        ) VALUES (?, ?, ?)
                                    """, (anime_id, recommended_id, rating))

                                    rec_count += 1

                    crawler.conn.commit()
                    success_count += 1
                    total_recommendations += rec_count
                    print(f"  ✅ 추천 {rec_count}개 저장")

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
        print(f"  총 추천: {total_recommendations}개")
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
