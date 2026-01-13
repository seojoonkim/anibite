"""
AniList API를 사용하여 캐릭터 정보가 없는 인기 애니메이션의 캐릭터 데이터 수집
"""
import requests
import sqlite3
import time
import sys

DB_PATH = '/Users/gimseojun/Documents/Git_Projects/anipass/data/anime.db'

def fetch_anime_characters(anime_id):
    """AniList API로 특정 애니메이션의 캐릭터 가져오기"""
    query = '''
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        characters(sort: ROLE, perPage: 25) {
          edges {
            role
            node {
              id
              name {
                full
                native
              }
              image {
                large
              }
              gender
              age
              dateOfBirth {
                year
                month
                day
              }
              bloodType
              description
              favourites
            }
            voiceActors(language: JAPANESE, sort: RELEVANCE) {
              id
              name {
                full
                native
              }
              image {
                large
              }
            }
          }
        }
      }
    }
    '''

    try:
        response = requests.post(
            'https://graphql.anilist.co',
            json={'query': query, 'variables': {'id': anime_id}},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("  ⚠️  Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return fetch_anime_characters(anime_id)
        else:
            print(f"  ❌ Error: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None


def crawl_missing_characters(limit=100, mode='popularity'):
    """
    캐릭터 정보가 없는 작품들의 캐릭터 데이터 수집

    Args:
        limit: 수집할 작품 수
        mode: 'popularity' (인기순) 또는 'user_rated' (사용자 평가 많은 순)
    """
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # 모드에 따라 다른 쿼리 실행
    if mode == 'user_rated':
        cursor.execute('''
            SELECT DISTINCT a.id, a.title_romaji, a.title_korean, COUNT(ur.id) as rating_count
            FROM anime a
            JOIN user_ratings ur ON a.id = ur.anime_id
            LEFT JOIN anime_character ac ON a.id = ac.anime_id
            WHERE ac.character_id IS NULL
            GROUP BY a.id
            ORDER BY rating_count DESC
            LIMIT ?
        ''', (limit,))
    else:  # popularity
        cursor.execute('''
            SELECT DISTINCT a.id, a.title_romaji, a.title_korean, a.popularity
            FROM anime a
            LEFT JOIN anime_character ac ON a.id = ac.anime_id
            WHERE ac.character_id IS NULL
            ORDER BY a.popularity DESC
            LIMIT ?
        ''', (limit,))

    anime_list = cursor.fetchall()
    print(f"\n{'='*60}")
    print(f"Found {len(anime_list)} anime without character data")
    print(f"Mode: {mode}")
    print(f"{'='*60}\n")

    success_count = 0
    fail_count = 0
    total_characters = 0

    for idx, row in enumerate(anime_list, 1):
        anime_id = row[0]
        title_romaji = row[1]
        title_korean = row[2]

        print(f"[{idx}/{len(anime_list)}] {title_korean or title_romaji} (ID: {anime_id})")

        data = fetch_anime_characters(anime_id)
        if not data or 'data' not in data or not data['data']['Media']:
            print(f"  ❌ Failed to fetch data")
            fail_count += 1
            continue

        characters = data['data']['Media']['characters']['edges']
        if not characters:
            print(f"  ℹ️  No characters found")
            fail_count += 1
            continue

        print(f"  Found {len(characters)} characters")

        char_inserted = 0
        for char_edge in characters:
            char = char_edge['node']
            role = char_edge['role']  # MAIN, SUPPORTING, BACKGROUND

            try:
                # Insert character
                cursor.execute('''
                    INSERT OR IGNORE INTO character (
                        id, name_full, name_native, image_url,
                        gender, age, blood_type, description, favourites
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    char['id'],
                    char['name']['full'],
                    char['name'].get('native'),
                    char['image']['large'],
                    char.get('gender'),
                    char.get('age'),
                    char.get('bloodType'),
                    char.get('description'),
                    char.get('favourites', 0)
                ))

                # Link character to anime
                cursor.execute('''
                    INSERT OR IGNORE INTO anime_character (anime_id, character_id, role)
                    VALUES (?, ?, ?)
                ''', (anime_id, char['id'], role))

                char_inserted += 1

                # Insert voice actors if available
                if char_edge.get('voiceActors'):
                    for va in char_edge['voiceActors'][:1]:  # 주요 성우 1명만
                        # Insert into staff table (not voice_actor)
                        cursor.execute('''
                            INSERT OR IGNORE INTO staff (
                                id, name_full, name_native, image_url
                            ) VALUES (?, ?, ?, ?)
                        ''', (
                            va['id'],
                            va['name']['full'],
                            va['name'].get('native'),
                            va['image']['large']
                        ))

                        # Link character to staff as voice actor
                        cursor.execute('''
                            INSERT OR IGNORE INTO character_voice_actor (
                                character_id, staff_id, anime_id, language
                            ) VALUES (?, ?, ?, ?)
                        ''', (char['id'], va['id'], anime_id, 'JAPANESE'))

            except Exception as e:
                print(f"  ⚠️  Error inserting character {char['name']['full']}: {e}")

        db.commit()
        print(f"  ✅ Saved {char_inserted} characters")
        success_count += 1
        total_characters += char_inserted

        # Rate limiting: ~90 requests/minute = 0.67초 간격
        time.sleep(0.7)

    db.close()

    print(f"\n{'='*60}")
    print(f"✨ Crawling completed!")
    print(f"Success: {success_count}/{len(anime_list)} anime")
    print(f"Failed: {fail_count}/{len(anime_list)} anime")
    print(f"Total characters collected: {total_characters}")
    print(f"{'='*60}\n")


def show_stats():
    """현재 캐릭터 데이터 통계 표시"""
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute('''
        SELECT
            COUNT(DISTINCT a.id) as total_anime,
            COUNT(DISTINCT CASE WHEN ac.character_id IS NOT NULL THEN a.id END) as with_chars,
            COUNT(DISTINCT CASE WHEN ac.character_id IS NULL THEN a.id END) as without_chars
        FROM anime a
        LEFT JOIN anime_character ac ON a.id = ac.anime_id
    ''')

    total, with_chars, without_chars = cursor.fetchone()
    percentage = (with_chars / total * 100) if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"Current Character Data Statistics")
    print(f"{'='*60}")
    print(f"Total anime: {total}")
    print(f"With characters: {with_chars} ({percentage:.1f}%)")
    print(f"Without characters: {without_chars} ({100-percentage:.1f}%)")
    print(f"{'='*60}\n")

    db.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Crawl missing anime characters from AniList')
    parser.add_argument('--limit', type=int, default=100, help='Number of anime to process (default: 100)')
    parser.add_argument('--mode', choices=['popularity', 'user_rated'], default='popularity',
                       help='Crawling mode: popularity (popular anime) or user_rated (most rated by users)')
    parser.add_argument('--stats', action='store_true', help='Show current statistics only')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        print("\n🚀 Starting character data collection...")
        show_stats()

        if args.yes:
            crawl_missing_characters(limit=args.limit, mode=args.mode)
            show_stats()
        else:
            confirm = input(f"\nProceed to crawl {args.limit} anime ({args.mode} mode)? [y/N]: ")
            if confirm.lower() == 'y':
                crawl_missing_characters(limit=args.limit, mode=args.mode)
                show_stats()
            else:
                print("Cancelled.")
