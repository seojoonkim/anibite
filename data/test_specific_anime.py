"""
특정 애니메이션 1개 크롤링 테스트
"""
from crawler import AnimeCrawler
from anilist_client import AniListClient

def test_specific_anime():
    # 새로 발견한 애니메이션 ID
    target_id = 187264

    print(f"🧪 애니메이션 ID {target_id} 크롤링 테스트\n")

    client = AniListClient()
    crawler = AnimeCrawler()
    crawler.connect()

    cursor = crawler.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime")
    before_count = cursor.fetchone()[0]
    print(f"📊 현재 애니메이션 수: {before_count}개\n")

    # 특정 ID로 검색
    print(f"🔍 ID {target_id} 정보 가져오기...")

    query = '''
    query ($id: Int) {
        Media(id: $id, type: ANIME) {
            id
            idMal
            title { romaji english native }
            type format status description
            season seasonYear episodes duration
            startDate { year month day }
            endDate { year month day }
            coverImage { large color }
            bannerImage
            averageScore meanScore popularity favourites trending
            source countryOfOrigin isAdult isLicensed
            siteUrl
            trailer { id site }
            updatedAt
            genres
            tags {
                id name description category rank
                isGeneralSpoiler isMediaSpoiler isAdult
            }
            studios {
                edges {
                    isMain
                    node {
                        id name isAnimationStudio siteUrl favourites
                    }
                }
            }
            relations {
                edges {
                    relationType
                    node { id type }
                }
            }
            recommendations(perPage: 10) {
                nodes {
                    rating
                    mediaRecommendation { id }
                }
            }
            externalLinks {
                site url type language
            }
            streamingEpisodes {
                title thumbnail url site
            }
            stats {
                scoreDistribution { score amount }
                statusDistribution { status amount }
            }
        }
    }
    '''

    data = client._make_request(query, {'id': target_id})

    if not data or 'Media' not in data:
        print("❌ API 호출 실패")
        crawler.close()
        return False

    anime = data['Media']
    title = anime.get('title', {}).get('romaji', 'Unknown')

    print(f"\n✅ API 응답 성공!")
    print(f"   ID: {anime['id']}")
    print(f"   제목: {title}")
    print(f"   영어: {anime.get('title', {}).get('english', 'N/A')}")
    print(f"   타입: {anime.get('format', 'N/A')}")
    print(f"   상태: {anime.get('status', 'N/A')}")
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
        SELECT title_romaji, popularity, average_score, format, status, episodes,
               (SELECT COUNT(*) FROM anime_genre WHERE anime_id = ?) as genre_count,
               (SELECT COUNT(*) FROM anime_tag WHERE anime_id = ?) as tag_count,
               (SELECT COUNT(*) FROM anime_studio WHERE anime_id = ?) as studio_count,
               (SELECT COUNT(*) FROM anime_relation WHERE anime_id = ?) as relation_count,
               cover_image_url, cover_image_local
        FROM anime WHERE id = ?
    """, (target_id, target_id, target_id, target_id, target_id))

    result = cursor.fetchone()

    print(f"\n✅ 저장 완료!")
    print(f"   애니메이션 수: {before_count} → {after_count} (+{after_count - before_count})")

    if result:
        print(f"\n📦 저장된 데이터 상세:")
        print(f"   제목: {result[0]}")
        print(f"   인기도: {result[1]:,}")
        print(f"   평점: {result[2]}")
        print(f"   포맷: {result[3]}")
        print(f"   상태: {result[4]}")
        print(f"   에피소드: {result[5]}")
        print(f"   장르: {result[6]}개")
        print(f"   태그: {result[7]}개")
        print(f"   스튜디오: {result[8]}개")
        print(f"   관련 작품: {result[9]}개")
        print(f"   커버 URL: {result[10][:60] if result[10] else 'None'}...")
        print(f"   로컬 경로: {result[11]}")

    crawler.close()
    return True

if __name__ == '__main__':
    success = test_specific_anime()
    print(f"\n{'='*60}")
    if success:
        print("✅ 테스트 성공: 크롤링이 정상 동작합니다!")
        print("   나머지 애니메이션도 크롤링할 수 있습니다.")
    else:
        print("⚠️  테스트 실패")
    print(f"{'='*60}")
