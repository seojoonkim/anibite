"""
외부 링크 데이터 크롤링
애니메이션의 공식 사이트, 트위터, 스트리밍 링크 등 수집
"""
import os
import sys

from crawler import AnimeCrawler

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🔗 외부 링크 데이터 크롤링                               ║
║   대상: 상위 3,000개 애니메이션                           ║
╚════════════════════════════════════════════════════════════╝
    """)

    crawler = AnimeCrawler()
    crawler.connect()

    try:
        # 이미 애니메이션 데이터가 있는 것들에 대해 외부 링크 추가
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
        total_links = 0

        for i, (anime_id, title) in enumerate(anime_list, 1):
            print(f"\n[{i}/{total}] {title} (ID: {anime_id})")

            try:
                # 외부 링크 데이터 가져오기
                query = """
                query ($id: Int) {
                    Media(id: $id) {
                        externalLinks {
                            url
                            site
                            type
                            language
                        }
                    }
                }
                """

                variables = {'id': anime_id}
                response = crawler.client._make_request(query, variables)

                if response and 'Media' in response:
                    external_links = response['Media'].get('externalLinks', [])
                    link_count = 0

                    for link in external_links:
                        url = link.get('url')
                        site = link.get('site')
                        link_type = link.get('type')
                        language = link.get('language')

                        if url:
                            # 외부 링크 저장
                            crawler.conn.execute("""
                                INSERT OR IGNORE INTO anime_external_link (
                                    anime_id, url, site, type, language
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                anime_id, url, site, link_type, language
                            ))

                            link_count += 1

                    crawler.conn.commit()
                    success_count += 1
                    total_links += link_count
                    print(f"  ✅ 링크 {link_count}개 저장")

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
        print(f"  총 링크: {total_links}개")
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
