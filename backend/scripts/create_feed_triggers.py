"""
Create triggers to keep feed_activities table in sync with source tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def create_feed_triggers():
    """Create triggers to automatically update feed_activities"""
    db = get_db()

    print("Creating triggers for feed_activities synchronization...\n")

    # ============================================================================
    # 1. ANIME RATING TRIGGERS
    # ============================================================================

    # Insert anime rating
    print("  - Creating trigger: anime_rating_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_insert
        AFTER INSERT ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_id, review_content
            )
            SELECT
                'anime_rating',
                NEW.user_id,
                NEW.anime_id,
                COALESCE(r.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                a.title_romaji,
                a.title_korean,
                COALESCE('/' || a.cover_image_local, a.cover_image_url),
                NEW.rating,
                r.id,
                r.content
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)

    # Update anime rating
    print("  - Creating trigger: anime_rating_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_update
        AFTER UPDATE ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            DELETE FROM feed_activities
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;

            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_id, review_content
            )
            SELECT
                'anime_rating',
                NEW.user_id,
                NEW.anime_id,
                COALESCE(r.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                a.title_romaji,
                a.title_korean,
                COALESCE('/' || a.cover_image_local, a.cover_image_url),
                NEW.rating,
                r.id,
                r.content
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)

    # Delete anime rating
    print("  - Creating trigger: anime_rating_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_delete
        AFTER DELETE ON user_ratings
        BEGIN
            DELETE FROM feed_activities
            WHERE activity_type = 'anime_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.anime_id;
        END
    """)

    # ============================================================================
    # 2. ANIME REVIEW TRIGGERS
    # ============================================================================

    print("  - Creating trigger: anime_review_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_review_insert
        AFTER INSERT ON user_reviews
        BEGIN
            -- Update existing anime_rating activity if it exists
            UPDATE feed_activities
            SET review_id = NEW.id,
                review_content = NEW.content,
                activity_time = NEW.created_at
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;

            -- If no rating exists, create anime_review activity
            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                review_id, review_content
            )
            SELECT
                'anime_review',
                NEW.user_id,
                NEW.anime_id,
                NEW.created_at,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                a.title_romaji,
                a.title_korean,
                COALESCE('/' || a.cover_image_local, a.cover_image_url),
                NEW.id,
                NEW.content
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            WHERE u.id = NEW.user_id
              AND NOT EXISTS (
                  SELECT 1 FROM user_ratings ur
                  WHERE ur.user_id = NEW.user_id
                    AND ur.anime_id = NEW.anime_id
                    AND ur.status = 'RATED'
                    AND ur.rating IS NOT NULL
              );
        END
    """)

    # ============================================================================
    # 3. CHARACTER RATING TRIGGERS
    # ============================================================================

    print("  - Creating trigger: character_rating_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_rating_insert
        AFTER INSERT ON character_ratings
        WHEN NEW.rating IS NOT NULL
        BEGIN
            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_id, review_content,
                anime_id, anime_title, anime_title_korean
            )
            SELECT
                'character_rating',
                NEW.user_id,
                NEW.character_id,
                COALESCE(rev.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                c.name_full,
                c.name_native,
                COALESCE('/' || c.image_local, c.image_url),
                NEW.rating,
                rev.id,
                rev.content,
                (SELECT a.id FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                (SELECT a.title_romaji FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                (SELECT a.title_korean FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
            FROM users u
            JOIN character c ON c.id = NEW.character_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN character_reviews rev ON rev.user_id = NEW.user_id AND rev.character_id = NEW.character_id
            WHERE u.id = NEW.user_id;
        END
    """)

    print("  - Creating trigger: character_rating_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_rating_update
        AFTER UPDATE ON character_ratings
        WHEN NEW.rating IS NOT NULL
        BEGIN
            DELETE FROM feed_activities
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;

            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_id, review_content,
                anime_id, anime_title, anime_title_korean
            )
            SELECT
                'character_rating',
                NEW.user_id,
                NEW.character_id,
                COALESCE(rev.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                c.name_full,
                c.name_native,
                COALESCE('/' || c.image_local, c.image_url),
                NEW.rating,
                rev.id,
                rev.content,
                (SELECT a.id FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                (SELECT a.title_romaji FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                (SELECT a.title_korean FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
            FROM users u
            JOIN character c ON c.id = NEW.character_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN character_reviews rev ON rev.user_id = NEW.user_id AND rev.character_id = NEW.character_id
            WHERE u.id = NEW.user_id;
        END
    """)

    print("  - Creating trigger: character_rating_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_rating_delete
        AFTER DELETE ON character_ratings
        BEGIN
            DELETE FROM feed_activities
            WHERE activity_type = 'character_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.character_id;
        END
    """)

    # ============================================================================
    # 4. CHARACTER REVIEW TRIGGERS
    # ============================================================================

    print("  - Creating trigger: character_review_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_review_insert
        AFTER INSERT ON character_reviews
        BEGIN
            -- Update existing character_rating activity if it exists
            UPDATE feed_activities
            SET review_id = NEW.id,
                review_content = NEW.content,
                activity_time = NEW.created_at
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;

            -- If no rating exists, create character_review activity
            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                review_id, review_content,
                anime_title, anime_title_korean
            )
            SELECT
                'character_review',
                NEW.user_id,
                NEW.character_id,
                NEW.created_at,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                c.name_full,
                c.name_native,
                COALESCE('/' || c.image_local, c.image_url),
                NEW.id,
                NEW.content,
                (SELECT a.title_romaji FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                (SELECT a.title_korean FROM anime a
                 JOIN anime_character ac ON a.id = ac.anime_id
                 WHERE ac.character_id = NEW.character_id
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
            FROM users u
            JOIN character c ON c.id = NEW.character_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            WHERE u.id = NEW.user_id
              AND NOT EXISTS (
                  SELECT 1 FROM character_ratings cr
                  WHERE cr.user_id = NEW.user_id
                    AND cr.character_id = NEW.character_id
                    AND cr.rating IS NOT NULL
              );
        END
    """)

    # ============================================================================
    # 5. USER POST TRIGGERS
    # ============================================================================

    print("  - Creating trigger: user_post_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_user_post_insert
        AFTER INSERT ON user_posts
        BEGIN
            INSERT INTO feed_activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                post_content
            )
            SELECT
                'user_post',
                NEW.user_id,
                NEW.id,
                NEW.created_at,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                NEW.content
            FROM users u
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            WHERE u.id = NEW.user_id;
        END
    """)

    print("  - Creating trigger: user_post_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_user_post_update
        AFTER UPDATE ON user_posts
        BEGIN
            UPDATE feed_activities
            SET post_content = NEW.content
            WHERE activity_type = 'user_post'
              AND user_id = NEW.user_id
              AND item_id = NEW.id;
        END
    """)

    print("  - Creating trigger: user_post_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_user_post_delete
        AFTER DELETE ON user_posts
        BEGIN
            DELETE FROM feed_activities
            WHERE activity_type = 'user_post'
              AND user_id = OLD.user_id
              AND item_id = OLD.id;
        END
    """)

    # ============================================================================
    # 6. USER PROFILE UPDATE TRIGGER (for denormalized fields)
    # ============================================================================

    print("  - Creating trigger: user_profile_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_user_profile_update
        AFTER UPDATE OF username, display_name, avatar_url ON users
        BEGIN
            UPDATE feed_activities
            SET username = NEW.username,
                display_name = NEW.display_name,
                avatar_url = NEW.avatar_url
            WHERE user_id = NEW.id;
        END
    """)

    print("\n✓ All triggers created successfully!")
    print("\nfeed_activities table will now be automatically synchronized with:")
    print("  - user_ratings (anime ratings)")
    print("  - user_reviews (anime reviews)")
    print("  - character_ratings (character ratings)")
    print("  - character_reviews (character reviews)")
    print("  - user_posts (user posts)")
    print("  - users (profile updates)")


if __name__ == "__main__":
    try:
        print("Creating triggers for feed_activities synchronization...\n")
        create_feed_triggers()
        print("\n✓ Setup completed! Feed activities will now be synchronized automatically.")
    except Exception as e:
        print(f"⚠ Trigger creation failed (may be already done): {e}")
        print("Continuing anyway...")
