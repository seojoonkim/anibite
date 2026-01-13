"""
애니메이션 1개 크롤링 테스트
"""
import sqlite3
from crawler import AnimeCrawler

def test_one_anime():
    print("🧪 애니메이션 1개 크롤링 테스트 시작\n")

    crawler = AnimeCrawler()
    crawler.connect()

    # 현재 상태 확인
    cursor = crawler.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime")
    before_count = cursor.fetchone()[0]
    print(f"📊 현재 애니메이션 수: {before_count}개\n")

    # 다음 페이지 계산 (페이지당 50개)
    next_page = (before_count // 50) + 1
    print(f"📄 페이지 {next_page}에서 1개 가져오기...\n")

    # API 호출
    data = crawler.client.get_popular_anime_page(page=next_page, per_page=1)

    if not data or 'Page' not in data:
        print("❌ API 호출 실패")
        crawler.close()
        return False

    media_list = data['Page']['media']

    if not media_list:
        print("❌ 더 이상 가져올 애니메이션이 없습니다")
        crawler.close()
        return False

    anime = media_list[0]
    anime_id = anime['id']
    title = anime.get('title', {}).get('romaji', 'Unknown')

    print(f"✅ API 응답 성공!")
    print(f"   ID: {anime_id}")
    print(f"   제목: {title}")
    print(f"   영어: {anime.get('title', {}).get('english', 'N/A')}")
    print(f"   인기도: {anime.get('popularity', 0):,}")
    print(f"   평점: {anime.get('averageScore', 'N/A')}")
    print(f"   에피소드: {anime.get('episodes', 'N/A')}")
    print(f"   장르: {', '.join(anime.get('genres', []))}")
    print(f"   커버 URL: {anime.get('coverImage', {}).get('large', 'N/A')[:50]}...")

    # DB에 저장
    print(f"\n💾 DB에 저장 중...")

    if anime_id in crawler.existing_anime_ids:
        print(f"⚠️  이미 존재하는 애니메이션입니다 (ID: {anime_id})")
        crawler.close()
        return False

    crawler._save_anime(anime)
    crawler.conn.commit()

    # 저장 확인
    cursor.execute("SELECT COUNT(*) FROM anime")
    after_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT title_romaji, popularity, average_score,
               (SELECT COUNT(*) FROM anime_genre WHERE anime_id = ?) as genre_count,
               (SELECT COUNT(*) FROM anime_tag WHERE anime_id = ?) as tag_count,
               (SELECT COUNT(*) FROM anime_studio WHERE anime_id = ?) as studio_count
        FROM anime WHERE id = ?
    """, (anime_id, anime_id, anime_id, anime_id))

    result = cursor.fetchone()

    print(f"\n✅ 저장 완료!")
    print(f"   애니메이션 수: {before_count} → {after_count} (+{after_count - before_count})")

    if result:
        print(f"\n📦 저장된 데이터:")
        print(f"   제목: {result[0]}")
        print(f"   인기도: {result[1]:,}")
        print(f"   평점: {result[2]}")
        print(f"   장르 수: {result[3]}")
        print(f"   태그 수: {result[4]}")
        print(f"   스튜디오 수: {result[5]}")

    crawler.close()
    return True

if __name__ == '__main__':
    success = test_one_anime()
    print(f"\n{'='*60}")
    if success:
        print("✅ 테스트 성공: 크롤링이 정상 동작합니다!")
    else:
        print("⚠️  테스트 실패 또는 중복 데이터")
    print(f"{'='*60}")
