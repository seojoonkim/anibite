"""
Create feed_activities table for optimized feed queries

This table stores all user activities (ratings, reviews, posts) in a single denormalized table
for fast feed queries without complex UNION and JOIN operations.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def create_feed_activities_table():
    """Create feed_activities table with indexes"""
    db = get_db()

    # Create table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS feed_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_type TEXT NOT NULL,  -- 'anime_rating', 'character_rating', 'anime_review', 'character_review', 'user_post'
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,  -- anime_id, character_id, or post_id
            activity_time DATETIME NOT NULL,

            -- Denormalized fields for fast display (avoid JOINs)
            username TEXT,
            display_name TEXT,
            avatar_url TEXT,
            otaku_score INTEGER DEFAULT 0,

            item_title TEXT,  -- anime/character title
            item_title_korean TEXT,
            item_image TEXT,

            rating REAL,  -- for ratings
            review_id INTEGER,  -- for reviews
            review_content TEXT,  -- for reviews
            post_content TEXT,  -- for user posts

            -- For character activities
            anime_id INTEGER,  -- which anime the character is from
            anime_title TEXT,
            anime_title_korean TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create indexes for fast queries
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feed_activity_time
        ON feed_activities(activity_time DESC)
    """)

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feed_user_activity
        ON feed_activities(user_id, activity_time DESC)
    """)

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feed_activity_type
        ON feed_activities(activity_type, activity_time DESC)
    """)

    print("✓ Created feed_activities table with indexes")


def migrate_existing_data():
    """Migrate existing activities to feed_activities table (idempotent)"""
    db = get_db()

    # Check if data already exists
    result = db.execute_query("SELECT COUNT(*) FROM feed_activities", fetch_one=True)
    existing_count = result[0] if result else 0

    if existing_count > 0:
        print(f"⚠ feed_activities table already has {existing_count} entries")
        print("  Skipping migration to avoid duplicates...")
        return

    print("Migrating existing data...")

    # 1. Migrate anime ratings
    print("  - Migrating anime ratings...")
    db.execute_query("""
        INSERT INTO feed_activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_id, review_content,
            anime_id, anime_title, anime_title_korean, post_content
        )
        SELECT
            'anime_rating' as activity_type,
            ur.user_id,
            ur.anime_id as item_id,
            COALESCE(r.created_at, ur.updated_at) as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            a.title_romaji as item_title,
            a.title_korean as item_title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
            ur.rating,
            r.id as review_id,
            r.content as review_content,
            NULL as anime_id,
            NULL as anime_title,
            NULL as anime_title_korean,
            NULL as post_content
        FROM user_ratings ur
        JOIN users u ON ur.user_id = u.id
        JOIN anime a ON ur.anime_id = a.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN user_reviews r ON ur.user_id = r.user_id AND ur.anime_id = r.anime_id
        WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
    """)

    # 2. Migrate character ratings
    print("  - Migrating character ratings...")
    db.execute_query("""
        INSERT INTO feed_activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_id, review_content,
            anime_id, anime_title, anime_title_korean, post_content
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
            c.name_korean as item_title_korean,
            COALESCE('/' || c.image_local, c.image_url) as item_image,
            cr.rating,
            rev.id as review_id,
            rev.content as review_content,
            (SELECT a.id FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_id,
            (SELECT a.title_romaji FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title,
            (SELECT a.title_korean FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title_korean,
            NULL as post_content
        FROM character_ratings cr
        JOIN users u ON cr.user_id = u.id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN character_reviews rev ON cr.user_id = rev.user_id AND cr.character_id = rev.character_id
        WHERE cr.rating IS NOT NULL
    """)

    # 3. Migrate anime reviews (without ratings)
    print("  - Migrating anime reviews...")
    db.execute_query("""
        INSERT INTO feed_activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_id, review_content,
            anime_id, anime_title, anime_title_korean, post_content
        )
        SELECT
            'anime_review' as activity_type,
            r.user_id,
            r.anime_id as item_id,
            r.created_at as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            a.title_romaji as item_title,
            a.title_korean as item_title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
            NULL as rating,
            r.id as review_id,
            r.content as review_content,
            NULL as anime_id,
            NULL as anime_title,
            NULL as anime_title_korean,
            NULL as post_content
        FROM user_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN anime a ON r.anime_id = a.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE NOT EXISTS (
            SELECT 1 FROM user_ratings ur
            WHERE ur.user_id = r.user_id
            AND ur.anime_id = r.anime_id
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
        )
    """)

    # 4. Migrate character reviews (without ratings)
    print("  - Migrating character reviews...")
    db.execute_query("""
        INSERT INTO feed_activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_id, review_content,
            anime_id, anime_title, anime_title_korean, post_content
        )
        SELECT
            'character_review' as activity_type,
            cr.user_id,
            cr.character_id as item_id,
            cr.created_at as activity_time,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            c.name_full as item_title,
            c.name_korean as item_title_korean,
            COALESCE('/' || c.image_local, c.image_url) as item_image,
            NULL as rating,
            cr.id as review_id,
            cr.content as review_content,
            NULL as anime_id,
            (SELECT a.title_romaji FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title,
            (SELECT a.title_korean FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title_korean,
            NULL as post_content
        FROM character_reviews cr
        JOIN users u ON cr.user_id = u.id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE NOT EXISTS (
            SELECT 1 FROM character_ratings cr2
            WHERE cr2.user_id = cr.user_id
            AND cr2.character_id = cr.character_id
            AND cr2.rating IS NOT NULL
        )
    """)

    # 5. Migrate user posts
    print("  - Migrating user posts...")
    db.execute_query("""
        INSERT INTO feed_activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            item_title, item_title_korean, item_image,
            rating, review_id, review_content,
            anime_id, anime_title, anime_title_korean, post_content
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
            NULL as item_title,
            NULL as item_title_korean,
            NULL as item_image,
            NULL as rating,
            NULL as review_id,
            NULL as review_content,
            NULL as anime_id,
            NULL as anime_title,
            NULL as anime_title_korean,
            up.content as post_content
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
    """)

    # Count total activities
    result = db.execute_query("SELECT COUNT(*) FROM feed_activities", fetch_one=True)
    total = result[0] if result else 0

    print(f"✓ Migrated {total} activities to feed_activities table")


if __name__ == "__main__":
    try:
        print("Creating feed_activities table for optimized feed queries...\n")

        create_feed_activities_table()
        migrate_existing_data()

        print("\n✓ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update feed_service.py to use feed_activities table")
        print("2. Add triggers to keep feed_activities in sync with source tables")
        print("3. Test feed query performance")
    except Exception as e:
        print(f"⚠ Migration failed (may be already done): {e}")
        print("Continuing anyway...")
