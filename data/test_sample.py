"""
샘플 데이터로 DB 구조 테스트
실제 크롤링 없이 DB 스키마와 조회 기능 검증
"""

import sqlite3
import json
import os

DB_PATH = 'anime_sample.db'

# 샘플 애니메이션 데이터
SAMPLE_ANIME = [
    {
        "id": 16498,
        "id_mal": 16498,
        "title_romaji": "Shingeki no Kyojin",
        "title_english": "Attack on Titan",
        "title_native": "進撃の巨人",
        "type": "ANIME",
        "format": "TV",
        "status": "FINISHED",
        "description": "Several hundred years ago, humans were nearly exterminated by titans...",
        "season": "SPRING",
        "season_year": 2013,
        "episodes": 25,
        "duration": 24,
        "start_date": "2013-04-07",
        "end_date": "2013-09-29",
        "cover_image_url": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx16498-C6FPmWm59CyP.jpg",
        "cover_image_color": "#e4a15d",
        "banner_image_url": "https://s4.anilist.co/file/anilistcdn/media/anime/banner/16498-8jpFCOcDmneG.jpg",
        "average_score": 84,
        "mean_score": 84,
        "popularity": 750000,
        "favourites": 120000,
        "source": "MANGA",
        "country_of_origin": "JP",
        "is_adult": 0,
        "site_url": "https://anilist.co/anime/16498",
        "genres": ["Action", "Drama", "Fantasy", "Mystery"],
        "tags": [
            {"id": 56, "name": "Shounen", "rank": 94},
            {"id": 82, "name": "Male Protagonist", "rank": 92},
            {"id": 104, "name": "Anti-Hero", "rank": 85},
        ],
        "studios": [
            {"id": 858, "name": "Wit Studio", "is_main": True},
        ],
    },
    {
        "id": 21,
        "id_mal": 21,
        "title_romaji": "ONE PIECE",
        "title_english": "ONE PIECE",
        "title_native": "ONE PIECE",
        "type": "ANIME",
        "format": "TV",
        "status": "RELEASING",
        "description": "Gol D. Roger was known as the Pirate King...",
        "season": "FALL",
        "season_year": 1999,
        "episodes": None,
        "duration": 24,
        "start_date": "1999-10-20",
        "cover_image_url": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx21-YCDoj1EkAxFn.jpg",
        "average_score": 87,
        "popularity": 550000,
        "source": "MANGA",
        "country_of_origin": "JP",
        "genres": ["Action", "Adventure", "Comedy", "Fantasy"],
        "tags": [
            {"id": 56, "name": "Shounen", "rank": 98},
            {"id": 303, "name": "Pirates", "rank": 95},
        ],
        "studios": [
            {"id": 18, "name": "Toei Animation", "is_main": True},
        ],
    },
    {
        "id": 1535,
        "id_mal": 1535,
        "title_romaji": "DEATH NOTE",
        "title_english": "Death Note",
        "title_native": "デスノート",
        "type": "ANIME",
        "format": "TV",
        "status": "FINISHED",
        "description": "A shinigami, as a god of death, can kill any person...",
        "season": "FALL",
        "season_year": 2006,
        "episodes": 37,
        "duration": 23,
        "start_date": "2006-10-04",
        "end_date": "2007-06-27",
        "cover_image_url": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx1535-lawCwhzhi96X.jpg",
        "average_score": 84,
        "popularity": 700000,
        "source": "MANGA",
        "country_of_origin": "JP",
        "genres": ["Mystery", "Psychological", "Supernatural", "Thriller"],
        "tags": [
            {"id": 56, "name": "Shounen", "rank": 90},
            {"id": 648, "name": "Crime", "rank": 88},
            {"id": 391, "name": "Philosophy", "rank": 75},
        ],
        "studios": [
            {"id": 11, "name": "Madhouse", "is_main": True},
        ],
    },
]

# 샘플 캐릭터 데이터
SAMPLE_CHARACTERS = [
    {
        "id": 45627,
        "name_full": "Eren Yeager",
        "name_native": "エレン・イェーガー",
        "description": "The main protagonist of Attack on Titan...",
        "gender": "Male",
        "age": "15-19",
        "image_url": "https://s4.anilist.co/file/anilistcdn/character/large/b45627-CR68RyZmddGG.png",
        "favourites": 75000,
        "anime_id": 16498,
        "role": "MAIN",
    },
    {
        "id": 46494,
        "name_full": "Mikasa Ackerman",
        "name_native": "ミカサ・アッカーマン",
        "description": "Mikasa is Eren's childhood friend...",
        "gender": "Female",
        "age": "15-19",
        "image_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46494-g998aW6LkzIu.png",
        "favourites": 95000,
        "anime_id": 16498,
        "role": "MAIN",
    },
    {
        "id": 71,
        "name_full": "Monkey D. Luffy",
        "name_native": "モンキー・D・ルフィ",
        "description": "The captain of the Straw Hat Pirates...",
        "gender": "Male",
        "age": "17-19",
        "image_url": "https://s4.anilist.co/file/anilistcdn/character/large/b71-3sEcNJnRvFaG.png",
        "favourites": 120000,
        "anime_id": 21,
        "role": "MAIN",
    },
    {
        "id": 80,
        "name_full": "Light Yagami",
        "name_native": "夜神 月",
        "description": "Light Yagami is the main protagonist...",
        "gender": "Male",
        "age": "17-23",
        "image_url": "https://s4.anilist.co/file/anilistcdn/character/large/b80-yxSm0oG6Uqzh.png",
        "favourites": 85000,
        "anime_id": 1535,
        "role": "MAIN",
    },
]

# 샘플 성우 데이터
SAMPLE_STAFF = [
    {
        "id": 95185,
        "name_full": "Yuuki Kaji",
        "name_native": "梶 裕貴",
        "description": "Famous voice actor known for many protagonist roles...",
        "gender": "Male",
        "language": "JAPANESE",
        "image_url": "https://s4.anilist.co/file/anilistcdn/staff/large/n95185-OPFTXkBKHrIp.png",
        "favourites": 45000,
        "characters": [45627],  # Eren
    },
    {
        "id": 95672,
        "name_full": "Yui Ishikawa",
        "name_native": "石川 由依",
        "description": "Voice actress known for Mikasa, Violet...",
        "gender": "Female",
        "language": "JAPANESE",
        "image_url": "https://s4.anilist.co/file/anilistcdn/staff/large/n95672-6pCc4Pg2P5PN.png",
        "favourites": 15000,
        "characters": [46494],  # Mikasa
    },
    {
        "id": 95158,
        "name_full": "Mayumi Tanaka",
        "name_native": "田中 真弓",
        "description": "Legendary voice actress, voice of Luffy since 1999...",
        "gender": "Female",
        "language": "JAPANESE",
        "image_url": "https://s4.anilist.co/file/anilistcdn/staff/large/95158.jpg",
        "favourites": 12000,
        "characters": [71],  # Luffy
    },
    {
        "id": 95015,
        "name_full": "Mamoru Miyano",
        "name_native": "宮野 真守",
        "description": "Popular voice actor and singer...",
        "gender": "Male",
        "language": "JAPANESE",
        "image_url": "https://s4.anilist.co/file/anilistcdn/staff/large/n95015-LiDNgOqbGmNQ.png",
        "favourites": 50000,
        "characters": [80],  # Light
    },
]


def create_sample_db():
    """샘플 DB 생성"""
    
    # 기존 DB 삭제
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 스키마 로드
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    cursor = conn.cursor()
    
    # 애니메이션 삽입
    print("📺 애니메이션 삽입 중...")
    for anime in SAMPLE_ANIME:
        cursor.execute('''
            INSERT INTO anime (
                id, id_mal, title_romaji, title_english, title_native,
                type, format, status, description,
                season, season_year, episodes, duration,
                start_date, end_date,
                cover_image_url, cover_image_color, banner_image_url,
                average_score, mean_score, popularity, favourites,
                source, country_of_origin, is_adult, site_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            anime['id'], anime.get('id_mal'), anime['title_romaji'],
            anime.get('title_english'), anime.get('title_native'),
            anime['type'], anime['format'], anime['status'], anime.get('description'),
            anime.get('season'), anime.get('season_year'), anime.get('episodes'), anime.get('duration'),
            anime.get('start_date'), anime.get('end_date'),
            anime.get('cover_image_url'), anime.get('cover_image_color'), anime.get('banner_image_url'),
            anime.get('average_score'), anime.get('mean_score'), anime.get('popularity'), anime.get('favourites'),
            anime.get('source'), anime.get('country_of_origin'), anime.get('is_adult', 0), anime.get('site_url'),
        ))
        
        # 장르
        for genre in anime.get('genres', []):
            cursor.execute('INSERT OR IGNORE INTO genre (name) VALUES (?)', (genre,))
            cursor.execute('SELECT id FROM genre WHERE name = ?', (genre,))
            genre_id = cursor.fetchone()[0]
            cursor.execute('INSERT INTO anime_genre (anime_id, genre_id) VALUES (?, ?)',
                          (anime['id'], genre_id))
        
        # 태그
        for tag in anime.get('tags', []):
            cursor.execute('''
                INSERT OR IGNORE INTO tag (id, name) VALUES (?, ?)
            ''', (tag['id'], tag['name']))
            cursor.execute('''
                INSERT INTO anime_tag (anime_id, tag_id, rank) VALUES (?, ?, ?)
            ''', (anime['id'], tag['id'], tag['rank']))
        
        # 스튜디오
        for studio in anime.get('studios', []):
            cursor.execute('''
                INSERT OR IGNORE INTO studio (id, name, is_animation_studio) VALUES (?, ?, 1)
            ''', (studio['id'], studio['name']))
            cursor.execute('''
                INSERT INTO anime_studio (anime_id, studio_id, is_main) VALUES (?, ?, ?)
            ''', (anime['id'], studio['id'], 1 if studio.get('is_main') else 0))
    
    # 캐릭터 삽입
    print("👤 캐릭터 삽입 중...")
    for char in SAMPLE_CHARACTERS:
        cursor.execute('''
            INSERT INTO character (
                id, name_full, name_native, description, gender, age, image_url, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            char['id'], char['name_full'], char.get('name_native'),
            char.get('description'), char.get('gender'), char.get('age'),
            char.get('image_url'), char.get('favourites', 0),
        ))
        
        cursor.execute('''
            INSERT INTO anime_character (anime_id, character_id, role) VALUES (?, ?, ?)
        ''', (char['anime_id'], char['id'], char['role']))
    
    # 성우 삽입
    print("🎤 성우 삽입 중...")
    for staff in SAMPLE_STAFF:
        cursor.execute('''
            INSERT INTO staff (
                id, name_full, name_native, description, gender, language, image_url, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            staff['id'], staff['name_full'], staff.get('name_native'),
            staff.get('description'), staff.get('gender'), staff.get('language'),
            staff.get('image_url'), staff.get('favourites', 0),
        ))
        
        # 캐릭터-성우 연결
        for char_id in staff.get('characters', []):
            # 캐릭터의 애니메이션 찾기
            cursor.execute('SELECT anime_id FROM anime_character WHERE character_id = ?', (char_id,))
            row = cursor.fetchone()
            if row:
                anime_id = row[0]
                cursor.execute('''
                    INSERT INTO character_voice_actor (character_id, staff_id, anime_id, language)
                    VALUES (?, ?, ?, ?)
                ''', (char_id, staff['id'], anime_id, staff['language']))
    
    conn.commit()
    
    # 통계 출력
    print("\n" + "="*60)
    print("📊 샘플 DB 생성 완료")
    print("="*60)
    
    tables = ['anime', 'character', 'staff', 'genre', 'tag', 'studio']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        print(f"   {table}: {cursor.fetchone()[0]}")
    
    conn.close()
    return DB_PATH


def test_queries():
    """조회 테스트"""
    print("\n" + "="*60)
    print("🔍 조회 테스트")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 인기 애니메이션
    print("\n📺 인기 애니메이션 Top 3:")
    cursor.execute('''
        SELECT title_romaji, title_english, average_score, popularity
        FROM anime ORDER BY popularity DESC LIMIT 3
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['title_english'] or row['title_romaji']}")
        print(f"     Score: {row['average_score']}, Popularity: {row['popularity']:,}")
    
    # 2. 장르별 애니
    print("\n🏷️ Action 장르 애니:")
    cursor.execute('''
        SELECT a.title_romaji, a.average_score
        FROM anime a
        JOIN anime_genre ag ON a.id = ag.anime_id
        JOIN genre g ON g.id = ag.genre_id
        WHERE g.name = 'Action'
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['title_romaji']} (Score: {row['average_score']})")
    
    # 3. 캐릭터 + 성우
    print("\n👤 인기 캐릭터 + 성우:")
    cursor.execute('''
        SELECT c.name_full as char_name, s.name_full as va_name, 
               a.title_romaji as anime, c.favourites
        FROM character c
        JOIN character_voice_actor cva ON c.id = cva.character_id
        JOIN staff s ON s.id = cva.staff_id
        JOIN anime a ON a.id = cva.anime_id
        ORDER BY c.favourites DESC
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['char_name']} ({row['anime']})")
        print(f"     CV: {row['va_name']}, ❤️ {row['favourites']:,}")
    
    # 4. 스튜디오별 작품
    print("\n🏢 스튜디오별 작품:")
    cursor.execute('''
        SELECT s.name as studio, GROUP_CONCAT(a.title_romaji) as anime_list
        FROM studio s
        JOIN anime_studio ast ON s.id = ast.studio_id
        JOIN anime a ON a.id = ast.anime_id
        WHERE ast.is_main = 1
        GROUP BY s.id
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['studio']}: {row['anime_list']}")
    
    # 5. 태그 검색
    print("\n🔖 'Shounen' 태그 애니:")
    cursor.execute('''
        SELECT a.title_romaji, at.rank
        FROM anime a
        JOIN anime_tag at ON a.id = at.anime_id
        JOIN tag t ON t.id = at.tag_id
        WHERE t.name = 'Shounen'
        ORDER BY at.rank DESC
    ''')
    for row in cursor.fetchall():
        print(f"   • {row['title_romaji']} (rank: {row['rank']})")
    
    conn.close()
    print("\n✅ 조회 테스트 완료!")


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🧪 샘플 데이터로 DB 테스트                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    create_sample_db()
    test_queries()
    
    # 파일 크기
    size = os.path.getsize(DB_PATH)
    print(f"\n📁 샘플 DB 크기: {size / 1024:.1f} KB")
    print(f"   (실제 3,000개 DB 예상: ~226 MB)")


if __name__ == '__main__':
    main()
