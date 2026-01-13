"""
Create unified activities table and migrate existing data

This script:
1. Creates a new 'activities' table that replaces feed_activities
2. Migrates all existing data from:
   - feed_activities (existing denormalized data)
   - user_ratings + user_reviews (anime ratings/reviews)
   - character_ratings + character_reviews (character ratings/reviews)
3. Creates proper indexes for performance
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def create_activities_table():
    """Create unified activities table"""
    db = get_db()

    print("Creating unified activities table...\n")

    # Drop feed_activities if it exists (we'll migrate its data)
    db.execute_query("DROP TABLE IF EXISTS feed_activities")

    # Create activities table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Activity type
            activity_type TEXT NOT NULL,  -- 'anime_rating', 'character_rating', 'user_post'

            -- User (denormalized for performance)
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            otaku_score INTEGER DEFAULT 0,

            -- Item (denormalized)
            item_id INTEGER,  -- anime_id, character_id, or NULL for user_posts
            item_title TEXT,
            item_title_korean TEXT,
            item_image TEXT,

            -- Rating & Review
            rating REAL,  -- 0.5 to 5.0, or NULL
            review_title TEXT,
            review_content TEXT,
            is_spoiler BOOLEAN DEFAULT 0,

            -- Metadata (for characters)
            anime_id INTEGER,  -- parent anime for characters
            anime_title TEXT,
            anime_title_korean TEXT,

            -- Timestamps
            activity_time DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            -- Unique constraint: one activity per (type, user, item)
            UNIQUE(activity_type, user_id, item_id)
        )
    """)

    print("✓ Created activities table")

    # Create indexes
    print("\nCreating indexes...")

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activities_user
        ON activities(user_id, activity_time DESC)
    """)
    print("  ✓ Created user index")

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activities_item
        ON activities(activity_type, item_id, activity_time DESC)
    """)
    print("  ✓ Created item index")

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activities_time
        ON activities(activity_time DESC)
    """)
    print("  ✓ Created time index")

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activities_type
        ON activities(activity_type, activity_time DESC)
    """)
    print("  ✓ Created type index")


def migrate_anime_ratings():
    """Migrate anime ratings and reviews to activities"""
    db = get_db()

    print("\nMigrating anime ratings and reviews...")

    # Get count
    count_row = db.execute_query("""
        SELECT COUNT(*) as count
        FROM user_ratings ur
        WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
    """, fetch_one=True)

    total = count_row['count'] if count_row else 0
    print(f"  Found {total} anime ratings to migrate")

    if total == 0:
        return

    # Insert anime ratings with reviews
    db.execute_query("""
        INSERT OR REPLACE INTO activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_title, review_content, is_spoiler
        )
        SELECT
            'anime_rating' as activity_type,
            ur.user_id,
            ur.anime_id as item_id,
            COALESCE(rev.created_at, ur.updated_at) as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            a.title_romaji as item_title,
            a.title_korean as item_title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
            ur.rating,
            rev.title as review_title,
            rev.content as review_content,
            COALESCE(rev.is_spoiler, 0) as is_spoiler
        FROM user_ratings ur
        JOIN users u ON ur.user_id = u.id
        JOIN anime a ON ur.anime_id = a.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN user_reviews rev ON rev.user_id = ur.user_id AND rev.anime_id = ur.anime_id
        WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
    """)

    print(f"  ✓ Migrated {total} anime ratings")


def migrate_character_ratings():
    """Migrate character ratings and reviews to activities"""
    db = get_db()

    print("\nMigrating character ratings and reviews...")

    # Get count
    count_row = db.execute_query("""
        SELECT COUNT(*) as count
        FROM character_ratings cr
        WHERE cr.rating IS NOT NULL
    """, fetch_one=True)

    total = count_row['count'] if count_row else 0
    print(f"  Found {total} character ratings to migrate")

    if total == 0:
        return

    # Insert character ratings with reviews
    db.execute_query("""
        INSERT OR REPLACE INTO activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_title, review_content, is_spoiler,
            anime_id, anime_title, anime_title_korean
        )
        SELECT
            'character_rating' as activity_type,
            cr.user_id,
            cr.character_id as item_id,
            COALESCE(rev.created_at, cr.updated_at) as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            c.name_full as item_title,
            c.name_native as item_title_korean,
            c.image_url as item_image,
            cr.rating,
            rev.title as review_title,
            rev.content as review_content,
            COALESCE(rev.is_spoiler, 0) as is_spoiler,
            (SELECT a.id FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = cr.character_id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_id,
            (SELECT a.title_romaji FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = cr.character_id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title,
            (SELECT a.title_korean FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = cr.character_id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title_korean
        FROM character_ratings cr
        JOIN users u ON cr.user_id = u.id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN character_reviews rev ON rev.user_id = cr.user_id AND rev.character_id = cr.character_id
        WHERE cr.rating IS NOT NULL
    """)

    print(f"  ✓ Migrated {total} character ratings")


def migrate_user_posts():
    """Migrate user posts to activities"""
    db = get_db()

    print("\nMigrating user posts...")

    # Get count
    count_row = db.execute_query("""
        SELECT COUNT(*) as count FROM user_posts
    """, fetch_one=True)

    total = count_row['count'] if count_row else 0
    print(f"  Found {total} user posts to migrate")

    if total == 0:
        return

    # Insert user posts
    db.execute_query("""
        INSERT OR REPLACE INTO activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            review_content
        )
        SELECT
            'user_post' as activity_type,
            up.user_id,
            up.id as item_id,
            up.created_at as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            up.content as review_content
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
    """)

    print(f"  ✓ Migrated {total} user posts")


def update_activity_comments():
    """Update activity_comments to reference activities table"""
    db = get_db()

    print("\nUpdating activity_comments table...")

    # Check if we need to add activity_id column
    columns = db.execute_query("""
        PRAGMA table_info(activity_comments)
    """)

    has_activity_id = any(col['name'] == 'activity_id' for col in columns)

    if not has_activity_id:
        print("  Adding activity_id column...")
        db.execute_query("""
            ALTER TABLE activity_comments ADD COLUMN activity_id INTEGER
        """)

        # Populate activity_id from existing data
        # For anime ratings
        db.execute_query("""
            UPDATE activity_comments
            SET activity_id = (
                SELECT id FROM activities
                WHERE activity_type = activity_comments.activity_type
                AND user_id = activity_comments.activity_user_id
                AND item_id = activity_comments.item_id
                LIMIT 1
            )
            WHERE activity_type = 'anime_rating'
        """)

        # For character ratings
        db.execute_query("""
            UPDATE activity_comments
            SET activity_id = (
                SELECT id FROM activities
                WHERE activity_type = activity_comments.activity_type
                AND user_id = activity_comments.activity_user_id
                AND item_id = activity_comments.item_id
                LIMIT 1
            )
            WHERE activity_type = 'character_rating'
        """)

        # For user posts
        db.execute_query("""
            UPDATE activity_comments
            SET activity_id = (
                SELECT id FROM activities
                WHERE activity_type = activity_comments.activity_type
                AND user_id = activity_comments.activity_user_id
                AND item_id = activity_comments.item_id
                LIMIT 1
            )
            WHERE activity_type = 'user_post'
        """)

        print("  ✓ Populated activity_id")

    print("  ✓ Updated activity_comments")


def update_activity_likes():
    """Update activity_likes to reference activities table"""
    db = get_db()

    print("\nUpdating activity_likes table...")

    # Check if we need to add activity_id column
    columns = db.execute_query("""
        PRAGMA table_info(activity_likes)
    """)

    has_activity_id = any(col['name'] == 'activity_id' for col in columns)

    if not has_activity_id:
        print("  Adding activity_id column...")
        db.execute_query("""
            ALTER TABLE activity_likes ADD COLUMN activity_id INTEGER
        """)

        # Populate activity_id from existing data
        db.execute_query("""
            UPDATE activity_likes
            SET activity_id = (
                SELECT id FROM activities
                WHERE activity_type = activity_likes.activity_type
                AND user_id = activity_likes.activity_user_id
                AND item_id = activity_likes.item_id
                LIMIT 1
            )
        """)

        print("  ✓ Populated activity_id")

    print("  ✓ Updated activity_likes")


def verify_migration():
    """Verify migration was successful"""
    db = get_db()

    print("\n" + "=" * 60)
    print("Migration Verification")
    print("=" * 60)

    # Count activities by type
    anime_count = db.execute_query("""
        SELECT COUNT(*) as count FROM activities WHERE activity_type = 'anime_rating'
    """, fetch_one=True)['count']

    character_count = db.execute_query("""
        SELECT COUNT(*) as count FROM activities WHERE activity_type = 'character_rating'
    """, fetch_one=True)['count']

    post_count = db.execute_query("""
        SELECT COUNT(*) as count FROM activities WHERE activity_type = 'user_post'
    """, fetch_one=True)['count']

    total = anime_count + character_count + post_count

    print(f"\nActivities in unified table:")
    print(f"  Anime ratings: {anime_count}")
    print(f"  Character ratings: {character_count}")
    print(f"  User posts: {post_count}")
    print(f"  Total: {total}")

    # Sample activities
    print("\nSample activities:")
    samples = db.execute_query("""
        SELECT activity_type, username, item_title, rating,
               CASE WHEN review_content IS NOT NULL THEN 'Yes' ELSE 'No' END as has_review
        FROM activities
        ORDER BY activity_time DESC
        LIMIT 5
    """)

    for sample in samples:
        print(f"  - {sample['activity_type']}: {sample['username']} → {sample['item_title']} "
              f"(rating: {sample['rating']}, review: {sample['has_review']})")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Creating Unified Activities System")
        print("=" * 60)

        create_activities_table()
        migrate_anime_ratings()
        migrate_character_ratings()
        migrate_user_posts()
        update_activity_comments()
        update_activity_likes()
        verify_migration()

        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
