"""
DB 분리 마이그레이션 스크립트

기존 anime.db를 3개의 DB로 분리:
- anime.db: 애니메이션 데이터 + 다국어 번역
- character.db: 캐릭터 데이터 + 다국어 번역
- users.db: 사용자/활동 데이터
"""
import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, ANIME_DB_PATH, CHARACTER_DB_PATH, USERS_DB_PATH

# 원본 백업에서 마이그레이션
BACKUP_PATH = DATA_DIR / "anime_backup.db"
OLD_DB_PATH = BACKUP_PATH  # 백업에서 마이그레이션


def create_anime_db():
    """애니메이션 DB 생성 (다국어 테이블 포함)"""
    print("Creating anime.db...")

    conn = sqlite3.connect(str(ANIME_DB_PATH))
    cursor = conn.cursor()

    # 애니메이션 기본 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY,
            id_mal INTEGER,
            title_romaji TEXT,
            title_english TEXT,
            title_native TEXT,
            type TEXT,
            format TEXT,
            status TEXT,
            description TEXT,
            season TEXT,
            season_year INTEGER,
            episodes INTEGER,
            duration INTEGER,
            start_date TEXT,
            end_date TEXT,
            cover_image_local TEXT,
            cover_image_url TEXT,
            cover_image_color TEXT,
            banner_image_url TEXT,
            average_score INTEGER,
            mean_score INTEGER,
            popularity INTEGER,
            favourites INTEGER,
            trending INTEGER,
            source TEXT,
            country_of_origin TEXT,
            is_adult BOOLEAN DEFAULT 0,
            is_licensed BOOLEAN DEFAULT 1,
            site_url TEXT,
            trailer_url TEXT,
            trailer_site TEXT,
            updated_at INTEGER,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            title_korean TEXT,
            title_korean_official INTEGER DEFAULT 0
        )
    """)

    # 다국어 번역 테이블 (지원 언어: en, ko, ja, zh)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_translations (
            anime_id INTEGER NOT NULL,
            language TEXT NOT NULL CHECK(language IN ('en', 'ko', 'ja', 'zh')),
            title TEXT,
            description TEXT,
            is_official BOOLEAN DEFAULT 0,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (anime_id, language),
            FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anime_trans_lang ON anime_translations(language)")

    # 장르
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS genre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_genre (
            anime_id INTEGER REFERENCES anime(id),
            genre_id INTEGER REFERENCES genre(id),
            PRIMARY KEY (anime_id, genre_id)
        )
    """)

    # 스튜디오
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studio (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_animation_studio BOOLEAN DEFAULT 1,
            site_url TEXT,
            favourites INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_studio (
            anime_id INTEGER REFERENCES anime(id),
            studio_id INTEGER REFERENCES studio(id),
            is_main BOOLEAN DEFAULT 0,
            PRIMARY KEY (anime_id, studio_id)
        )
    """)

    # 스태프
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY,
            name_first TEXT,
            name_last TEXT,
            name_full TEXT,
            name_native TEXT,
            description TEXT,
            gender TEXT,
            age INTEGER,
            date_of_birth TEXT,
            date_of_death TEXT,
            home_town TEXT,
            blood_type TEXT,
            years_active_start INTEGER,
            years_active_end INTEGER,
            primary_occupations TEXT,
            language TEXT,
            image_url TEXT,
            image_local TEXT,
            favourites INTEGER DEFAULT 0,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_staff (
            anime_id INTEGER REFERENCES anime(id),
            staff_id INTEGER REFERENCES staff(id),
            role TEXT,
            PRIMARY KEY (anime_id, staff_id, role)
        )
    """)

    # 태그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            rank INTEGER,
            is_general_spoiler BOOLEAN DEFAULT 0,
            is_media_spoiler BOOLEAN DEFAULT 0,
            is_adult BOOLEAN DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_tag (
            anime_id INTEGER REFERENCES anime(id),
            tag_id INTEGER REFERENCES tag(id),
            rank INTEGER,
            is_spoiler BOOLEAN DEFAULT 0,
            PRIMARY KEY (anime_id, tag_id)
        )
    """)

    # 외부 링크
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_external_link (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER REFERENCES anime(id),
            site TEXT,
            url TEXT,
            type TEXT,
            language TEXT
        )
    """)

    # 관련 작품
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_relation (
            anime_id INTEGER REFERENCES anime(id),
            related_anime_id INTEGER,
            relation_type TEXT,
            PRIMARY KEY (anime_id, related_anime_id)
        )
    """)

    # 추천
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_recommendation (
            anime_id INTEGER REFERENCES anime(id),
            recommended_anime_id INTEGER,
            rating INTEGER,
            PRIMARY KEY (anime_id, recommended_anime_id)
        )
    """)

    # 점수 분포
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_score_distribution (
            anime_id INTEGER REFERENCES anime(id),
            score INTEGER,
            amount INTEGER,
            PRIMARY KEY (anime_id, score)
        )
    """)

    # 상태 분포
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_status_distribution (
            anime_id INTEGER REFERENCES anime(id),
            status TEXT,
            amount INTEGER,
            PRIMARY KEY (anime_id, status)
        )
    """)

    # 스트리밍 에피소드
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_streaming_episode (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER REFERENCES anime(id),
            title TEXT,
            thumbnail_url TEXT,
            url TEXT,
            site TEXT
        )
    """)

    # 크롤링 메타
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 추천 캐시
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_cache (
            user_id INTEGER,
            anime_id INTEGER,
            score REAL,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, anime_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"✓ anime.db created at {ANIME_DB_PATH}")


def create_character_db():
    """캐릭터 DB 생성 (다국어 테이블 포함)"""
    print("Creating character.db...")

    conn = sqlite3.connect(str(CHARACTER_DB_PATH))
    cursor = conn.cursor()

    # 캐릭터 기본 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character (
            id INTEGER PRIMARY KEY,
            name_first TEXT,
            name_last TEXT,
            name_full TEXT,
            name_native TEXT,
            name_alternative TEXT,
            name_korean TEXT,
            image_url TEXT,
            description TEXT,
            gender TEXT,
            date_of_birth TEXT,
            age TEXT,
            blood_type TEXT,
            site_url TEXT,
            favourites INTEGER DEFAULT 0,
            mod_notes TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 캐릭터 다국어 번역 테이블 (지원 언어: en, ko, ja, zh)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_translations (
            character_id INTEGER NOT NULL,
            language TEXT NOT NULL CHECK(language IN ('en', 'ko', 'ja', 'zh')),
            name TEXT,
            description TEXT,
            is_official BOOLEAN DEFAULT 0,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (character_id, language),
            FOREIGN KEY (character_id) REFERENCES character(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_char_trans_lang ON character_translations(language)")

    # 애니메이션-캐릭터 연결
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anime_character (
            anime_id INTEGER NOT NULL,
            character_id INTEGER REFERENCES character(id),
            role TEXT,
            PRIMARY KEY (anime_id, character_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anime_char_anime ON anime_character(anime_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anime_char_char ON anime_character(character_id)")

    # 성우
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_voice_actor (
            character_id INTEGER REFERENCES character(id),
            staff_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL,
            language TEXT DEFAULT 'JAPANESE',
            PRIMARY KEY (character_id, staff_id, anime_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"✓ character.db created at {CHARACTER_DB_PATH}")


def create_users_db():
    """사용자 DB 생성"""
    print("Creating users.db...")

    conn = sqlite3.connect(str(USERS_DB_PATH))
    cursor = conn.cursor()

    # 사용자
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            bio TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_verified BOOLEAN DEFAULT 0,
            verification_token TEXT,
            verification_token_expires DATETIME,
            last_notification_check TIMESTAMP NULL,
            preferred_language TEXT DEFAULT 'ko'
        )
    """)

    # 세션
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 애니메이션 평점
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            anime_id INTEGER NOT NULL,
            rating REAL CHECK(rating >= 0.5 AND rating <= 5.0),
            status TEXT CHECK(status IN ('RATED', 'WANT_TO_WATCH', 'PASS')) DEFAULT 'RATED',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id)
        )
    """)

    # 애니메이션 리뷰
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            anime_id INTEGER NOT NULL,
            rating_id INTEGER REFERENCES user_ratings(id) ON DELETE CASCADE,
            title TEXT,
            content TEXT NOT NULL,
            is_spoiler BOOLEAN DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_id)
        )
    """)

    # 캐릭터 평점
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            character_id INTEGER NOT NULL,
            rating REAL CHECK(rating >= 0.5 AND rating <= 5.0),
            status TEXT CHECK(status IN ('RATED', 'WANT_TO_KNOW', 'NOT_INTERESTED')) DEFAULT 'RATED',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id)
        )
    """)

    # 캐릭터 리뷰
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            character_id INTEGER NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            is_spoiler BOOLEAN DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id)
        )
    """)

    # 팔로우
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(follower_id, following_id),
            CHECK(follower_id != following_id)
        )
    """)

    # 사용자 포스트
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 사용자 통계
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            total_rated INTEGER DEFAULT 0,
            total_want_to_watch INTEGER DEFAULT 0,
            total_pass INTEGER DEFAULT 0,
            average_rating REAL,
            total_reviews INTEGER DEFAULT 0,
            total_watch_time_minutes INTEGER DEFAULT 0,
            otaku_score REAL DEFAULT 0,
            favorite_genre TEXT,
            total_character_ratings INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 활동 피드
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            otaku_score INTEGER DEFAULT 0,
            item_id INTEGER,
            item_title TEXT,
            item_title_korean TEXT,
            item_image TEXT,
            rating REAL,
            review_title TEXT,
            review_content TEXT,
            is_spoiler BOOLEAN DEFAULT 0,
            anime_id INTEGER,
            anime_title TEXT,
            anime_title_korean TEXT,
            activity_time DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            item_year INTEGER,
            metadata TEXT,
            UNIQUE(activity_type, user_id, item_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_time ON activities(activity_time DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_user ON activities(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type)")

    # 활동 북마크
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, activity_id)
        )
    """)

    # 활동 댓글
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activity_type TEXT NOT NULL,
            activity_user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            activity_id INTEGER,
            content TEXT NOT NULL,
            parent_comment_id INTEGER REFERENCES activity_comments(id) ON DELETE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 활동 좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activity_type TEXT NOT NULL,
            activity_user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            activity_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, activity_type, activity_user_id, item_id)
        )
    """)

    # 리뷰 댓글/좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            review_id INTEGER NOT NULL,
            review_type TEXT NOT NULL CHECK(review_type IN ('anime', 'anime_aspect', 'character', 'staff')) DEFAULT 'anime',
            parent_comment_id INTEGER REFERENCES review_comments(id) ON DELETE CASCADE,
            content TEXT NOT NULL CHECK(LENGTH(content) >= 1 AND LENGTH(content) <= 1000),
            likes_count INTEGER DEFAULT 0,
            depth INTEGER DEFAULT 1 CHECK(depth IN (1, 2)),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(review_id, user_id)
        )
    """)

    # 캐릭터 리뷰 좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_review_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES character_reviews(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(review_id, user_id)
        )
    """)

    # 댓글 좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(comment_id, user_id)
        )
    """)

    # 알림
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            activity_id INTEGER,
            comment_id INTEGER,
            content TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # UI 번역 테이블 (웹사이트 다국어 지원)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ui_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            language TEXT NOT NULL CHECK(language IN ('en', 'ko', 'ja', 'zh')),
            value TEXT NOT NULL,
            context TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(key, language)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_trans_key ON ui_translations(key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_trans_lang ON ui_translations(language)")

    # 마이그레이션 히스토리
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"✓ users.db created at {USERS_DB_PATH}")


def migrate_data_from_old_db():
    """기존 anime.db에서 데이터 마이그레이션"""
    if not os.path.exists(OLD_DB_PATH):
        print(f"Old database not found at {OLD_DB_PATH}")
        return

    print(f"\nMigrating data from {OLD_DB_PATH}...")

    old_conn = sqlite3.connect(str(OLD_DB_PATH))
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    # 1. anime.db로 데이터 복사
    print("\n[1/3] Migrating anime data...")
    anime_conn = sqlite3.connect(str(ANIME_DB_PATH))
    anime_cursor = anime_conn.cursor()

    anime_tables = [
        'anime', 'genre', 'anime_genre', 'studio', 'anime_studio',
        'staff', 'anime_staff', 'tag', 'anime_tag', 'anime_external_link',
        'anime_relation', 'anime_recommendation', 'anime_score_distribution',
        'anime_status_distribution', 'anime_streaming_episode', 'crawl_meta',
        'recommendation_cache'
    ]

    for table in anime_tables:
        try:
            old_cursor.execute(f"SELECT * FROM {table}")
            rows = old_cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in old_cursor.description]
                placeholders = ','.join(['?' for _ in columns])
                anime_cursor.executemany(
                    f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    [tuple(row) for row in rows]
                )
                print(f"  ✓ {table}: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠ {table}: {e}")

    # 기존 한국어 제목을 anime_translations로 복사
    old_cursor.execute("SELECT id, title_korean FROM anime WHERE title_korean IS NOT NULL")
    korean_titles = old_cursor.fetchall()
    for row in korean_titles:
        anime_cursor.execute(
            "INSERT OR REPLACE INTO anime_translations (anime_id, language, title, is_official) VALUES (?, 'ko', ?, 1)",
            (row[0], row[1])
        )
    print(f"  ✓ anime_translations (ko): {len(korean_titles)} rows")

    anime_conn.commit()
    anime_conn.close()

    # 2. character.db로 데이터 복사
    print("\n[2/3] Migrating character data...")
    char_conn = sqlite3.connect(str(CHARACTER_DB_PATH))
    char_cursor = char_conn.cursor()

    char_tables = ['character', 'anime_character', 'character_voice_actor']

    for table in char_tables:
        try:
            old_cursor.execute(f"SELECT * FROM {table}")
            rows = old_cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in old_cursor.description]
                # character_translations에 없는 컬럼만 필터
                if table == 'character':
                    valid_cols = ['id', 'name_first', 'name_last', 'name_full', 'name_native',
                                  'name_alternative', 'name_korean', 'image_url', 'description',
                                  'gender', 'date_of_birth', 'age', 'blood_type', 'site_url',
                                  'favourites', 'mod_notes', 'crawled_at']
                    columns = [c for c in columns if c in valid_cols]
                placeholders = ','.join(['?' for _ in columns])

                for row in rows:
                    row_dict = dict(row)
                    values = [row_dict.get(c) for c in columns]
                    char_cursor.execute(
                        f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        values
                    )
                print(f"  ✓ {table}: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠ {table}: {e}")

    # 기존 한국어 이름을 character_translations로 복사
    old_cursor.execute("SELECT id, name_korean FROM character WHERE name_korean IS NOT NULL")
    korean_names = old_cursor.fetchall()
    for row in korean_names:
        char_cursor.execute(
            "INSERT OR REPLACE INTO character_translations (character_id, language, name, is_official) VALUES (?, 'ko', ?, 1)",
            (row[0], row[1])
        )
    print(f"  ✓ character_translations (ko): {len(korean_names)} rows")

    char_conn.commit()
    char_conn.close()

    # 3. users.db로 데이터 복사
    print("\n[3/3] Migrating user data...")
    users_conn = sqlite3.connect(str(USERS_DB_PATH))
    users_cursor = users_conn.cursor()

    user_tables = [
        'users', 'user_sessions', 'user_ratings', 'user_reviews', 'user_follows',
        'user_posts', 'user_stats', 'activities', 'activity_bookmarks',
        'activity_comments', 'activity_likes', 'character_ratings',
        'character_reviews', 'character_review_likes', 'review_comments',
        'review_likes', 'comment_likes', 'notifications', 'migration_history'
    ]

    for table in user_tables:
        try:
            old_cursor.execute(f"SELECT * FROM {table}")
            rows = old_cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in old_cursor.description]
                placeholders = ','.join(['?' for _ in columns])
                users_cursor.executemany(
                    f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    [tuple(row) for row in rows]
                )
                print(f"  ✓ {table}: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠ {table}: {e}")

    users_conn.commit()
    users_conn.close()

    old_conn.close()
    print("\n✓ Migration complete!")


def verify_migration():
    """마이그레이션 검증"""
    print("\n=== Verifying migration ===")

    # anime.db
    conn = sqlite3.connect(str(ANIME_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime")
    print(f"anime.db - anime: {cursor.fetchone()[0]} rows")
    cursor.execute("SELECT COUNT(*) FROM anime_translations")
    print(f"anime.db - anime_translations: {cursor.fetchone()[0]} rows")
    conn.close()

    # character.db
    conn = sqlite3.connect(str(CHARACTER_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM character")
    print(f"character.db - character: {cursor.fetchone()[0]} rows")
    cursor.execute("SELECT COUNT(*) FROM character_translations")
    print(f"character.db - character_translations: {cursor.fetchone()[0]} rows")
    conn.close()

    # users.db
    conn = sqlite3.connect(str(USERS_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"users.db - users: {cursor.fetchone()[0]} rows")
    cursor.execute("SELECT COUNT(*) FROM user_ratings")
    print(f"users.db - user_ratings: {cursor.fetchone()[0]} rows")
    cursor.execute("SELECT COUNT(*) FROM activities")
    print(f"users.db - activities: {cursor.fetchone()[0]} rows")
    conn.close()

    # File sizes
    print(f"\nFile sizes:")
    for path, name in [(ANIME_DB_PATH, 'anime.db'), (CHARACTER_DB_PATH, 'character.db'), (USERS_DB_PATH, 'users.db')]:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  {name}: {size_mb:.2f} MB")


def main():
    print("=" * 50)
    print("Database Split Migration")
    print("=" * 50)

    # 백업 확인
    if not os.path.exists(BACKUP_PATH):
        print(f"ERROR: Backup database not found at {BACKUP_PATH}")
        print("Please ensure anime_backup.db exists before running migration.")
        return

    # DB 생성
    create_anime_db()
    create_character_db()
    create_users_db()

    # 데이터 마이그레이션
    migrate_data_from_old_db()

    # 검증
    verify_migration()

    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
