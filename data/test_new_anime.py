"""
새 애니메이션 1개 크롤링 테스트 (중복 건너뛰기)
"""
import sqlite3
from crawler import AnimeCrawler

def test_new_anime():
    print("🧪 새 애니메이션 1개 크롤링 테스트\n")

    crawler = AnimeCrawler()
    crawler.connect()

    # 현재 상태 확인
    cursor = crawler.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime")
    before_count = cursor.fetchone()[0]
    print(f"📊 현재 애니메이션 수: {before_count}개\n")

    # 페이지 60부터 시작해서 새로운 애니 찾기
    found = False
    for page in range(60, 65):
        print(f"📄 페이지 {page} 확인 중...")

        data = crawler.client.get_popular_anime_page(page=page, per_page=5)

        if not data or 'Page' not in data:
            print(f"   ❌ API 호출 실패")
            continue

        media_list = data['Page']['media']

        for anime in media_list:
            anime_id = anime['id']

            if anime_id not in crawler.existing_anime_ids:
                # 새로운 애니메이션 발견!
                title = anime.get('title', {}).get('romaji', 'Unknown')

                print(f"\n✅ 새로운 애니메이션 발견!")
                print(f"   ID: {anime_id}")
                print(f"   제목: {title}")
                print(f"   영어: {anime.get('title', {}).get('english', 'N/A')}")
                print(f"   인기도: {anime.get('popularity', 0):,}")
                print(f"   평점: {anime.get('averageScore', 'N/A')}")
                print(f"   에피소드: {anime.get('episodes', 'N/A')}")
                print(f"   장르: {', '.join(anime.get('genres', []))}")

                cover_url = anime.get('coverImage', {}).get('large', 'N/A')
                if len(cover_url) > 60:
                    cover_url = cover_url[:60] + "..."
                print(f"   커버 URL: {cover_url}")

                # DB에 저장
                print(f"\n💾 DB에 저장 중...")
                crawler._save_anime(anime)
                crawler.conn.commit()

                # 저장 확인
                cursor.execute("SELECT COUNT(*) FROM anime")
                after_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT title_romaji, popularity, average_score,
                           (SELECT COUNT(*) FROM anime_genre WHERE anime_id = ?) as genre_count,
                           (SELECT COUNT(*) FROM anime_tag WHERE anime_id = ?) as tag_count,
                           (SELECT COUNT(*) FROM anime_studio WHERE anime_id = ?) as studio_count,
                           (SELECT COUNT(*) FROM anime_relation WHERE anime_id = ?) as relation_count
                    FROM anime WHERE id = ?
                """, (anime_id, anime_id, anime_id, anime_id, anime_id))

                result = cursor.fetchone()

                print(f"\n✅ 저장 완료!")
                print(f"   애니메이션 수: {before_count} → {after_count} (+{after_count - before_count})")

                if result:
                    print(f"\n📦 저장된 데이터:")
                    print(f"   제목: {result[0]}")
                    print(f"   인기도: {result[1]:,}")
                    print(f"   평점: {result[2]}")
                    print(f"   장르: {result[3]}개")
                    print(f"   태그: {result[4]}개")
                    print(f"   스튜디오: {result[5]}개")
                    print(f"   관련 작품: {result[6]}개")

                found = True
                break

        if found:
            break

    crawler.close()
    return found

if __name__ == '__main__':
    success = test_new_anime()
    print(f"\n{'='*60}")
    if success:
        print("✅ 테스트 성공: 크롤링이 정상 동작합니다!")
    else:
        print("⚠️  새로운 애니메이션을 찾지 못했습니다")
    print(f"{'='*60}")
