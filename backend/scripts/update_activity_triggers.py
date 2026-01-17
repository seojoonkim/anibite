"""
Update triggers to sync with unified activities table

This replaces the old feed_activities triggers with new ones that:
1. Use the 'activities' table instead of 'feed_activities'
2. Include review content (title + content) in the activities
3. Handle review updates properly
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def drop_old_triggers():
    """Drop old feed_activities triggers"""
    db = get_db()

    print("Dropping old triggers...")

    old_triggers = [
        'trg_anime_rating_insert',
        'trg_anime_rating_update',
        'trg_anime_rating_delete',
        'trg_anime_review_insert',
        'trg_character_rating_insert',
        'trg_character_rating_update',
        'trg_character_rating_delete',
        'trg_character_review_insert',
        'trg_user_post_insert',
        'trg_user_post_update',
        'trg_user_post_delete',
        'trg_user_profile_update'
    ]

    for trigger_name in old_triggers:
        db.execute_query(f"DROP TRIGGER IF EXISTS {trigger_name}")
        print(f"  ✓ Dropped {trigger_name}")


def create_activity_triggers():
    """Create new activity triggers"""
    db = get_db()

    print("\nCreating new activity triggers...\n")

    # ============================================================================
    # 1. ANIME RATING TRIGGERS
    # ============================================================================

    print("  - Creating trigger: anime_rating_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_insert
        AFTER INSERT ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            -- Delete existing entry first to avoid duplicates
            DELETE FROM activities
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;

            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler
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
                r.title,
                r.content,
                COALESCE(r.is_spoiler, 0)
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)

    print("  - Creating trigger: anime_rating_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_update
        AFTER UPDATE ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            DELETE FROM activities
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;

            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler
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
                r.title,
                r.content,
                COALESCE(r.is_spoiler, 0)
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)

    print("  - Creating trigger: anime_rating_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_rating_delete
        AFTER DELETE ON user_ratings
        BEGIN
            DELETE FROM activities
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
            -- Update existing anime_rating activity
            UPDATE activities
            SET review_title = NEW.title,
                review_content = NEW.content,
                is_spoiler = NEW.is_spoiler,
                activity_time = NEW.created_at
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;
        END
    """)

    print("  - Creating trigger: anime_review_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_review_update
        AFTER UPDATE ON user_reviews
        BEGIN
            UPDATE activities
            SET review_title = NEW.title,
                review_content = NEW.content,
                is_spoiler = NEW.is_spoiler,
                updated_at = CURRENT_TIMESTAMP
            WHERE activity_type = 'anime_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.anime_id;
        END
    """)

    print("  - Creating trigger: anime_review_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_anime_review_delete
        AFTER DELETE ON user_reviews
        BEGIN
            -- Remove review content but keep rating
            UPDATE activities
            SET review_title = NULL,
                review_content = NULL,
                is_spoiler = 0
            WHERE activity_type = 'anime_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.anime_id;
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
            DELETE FROM activities
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;

            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
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
                c.name_korean,
                c.image_url,
                NEW.rating,
                rev.title,
                rev.content,
                COALESCE(rev.is_spoiler, 0),
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
            DELETE FROM activities
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;

            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
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
                c.name_korean,
                c.image_url,
                NEW.rating,
                rev.title,
                rev.content,
                COALESCE(rev.is_spoiler, 0),
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
            DELETE FROM activities
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
            UPDATE activities
            SET review_title = NEW.title,
                review_content = NEW.content,
                is_spoiler = NEW.is_spoiler,
                activity_time = NEW.created_at
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;
        END
    """)

    print("  - Creating trigger: character_review_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_review_update
        AFTER UPDATE ON character_reviews
        BEGIN
            UPDATE activities
            SET review_title = NEW.title,
                review_content = NEW.content,
                is_spoiler = NEW.is_spoiler,
                updated_at = CURRENT_TIMESTAMP
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;
        END
    """)

    print("  - Creating trigger: character_review_delete")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_review_delete
        AFTER DELETE ON character_reviews
        BEGIN
            UPDATE activities
            SET review_title = NULL,
                review_content = NULL,
                is_spoiler = 0
            WHERE activity_type = 'character_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.character_id;
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
            DELETE FROM activities
            WHERE activity_type = 'user_post'
              AND user_id = NEW.user_id
              AND item_id = NEW.id;

            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                review_content
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
            UPDATE activities
            SET review_content = NEW.content,
                updated_at = CURRENT_TIMESTAMP
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
            DELETE FROM activities
            WHERE activity_type = 'user_post'
              AND user_id = OLD.user_id
              AND item_id = OLD.id;
        END
    """)

    # ============================================================================
    # 6. USER PROFILE UPDATE TRIGGER
    # ============================================================================

    print("  - Creating trigger: user_profile_update")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_user_profile_update
        AFTER UPDATE OF username, display_name, avatar_url ON users
        BEGIN
            UPDATE activities
            SET username = NEW.username,
                display_name = NEW.display_name,
                avatar_url = NEW.avatar_url
            WHERE user_id = NEW.id;
        END
    """)

    print("\n✓ All triggers created successfully!")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Updating Activity Triggers")
        print("=" * 60)

        drop_old_triggers()
        create_activity_triggers()

        print("\n" + "=" * 60)
        print("✓ Triggers updated successfully!")
        print("=" * 60)
        print("\nActivities table will now be automatically synchronized with:")
        print("  - user_ratings (anime ratings)")
        print("  - user_reviews (anime reviews)")
        print("  - character_ratings (character ratings)")
        print("  - character_reviews (character reviews)")
        print("  - user_posts (user posts)")
        print("  - users (profile updates)")

    except Exception as e:
        print(f"\n✗ Trigger update failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
