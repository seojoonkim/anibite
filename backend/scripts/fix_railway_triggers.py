"""
Fix Railway triggers to use INSERT OR REPLACE
Railway 트리거를 INSERT OR REPLACE로 수정하여 UNIQUE constraint 에러 방지
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def fix_triggers():
    """트리거를 재생성하여 INSERT OR REPLACE 사용"""

    print("Dropping old triggers...")

    # Drop existing triggers
    triggers_to_drop = [
        'trg_anime_rating_insert',
        'trg_anime_rating_update',
        'trg_anime_rating_delete',
        'trg_character_rating_insert',
        'trg_character_rating_update',
        'trg_character_rating_delete',
        'trg_user_post_insert',
        'trg_user_post_update',
        'trg_user_post_delete'
    ]

    for trigger_name in triggers_to_drop:
        try:
            db.execute_update(f"DROP TRIGGER IF EXISTS {trigger_name}")
            print(f"✓ Dropped {trigger_name}")
        except Exception as e:
            print(f"✗ Failed to drop {trigger_name}: {e}")

    print("\nCreating new triggers with INSERT OR REPLACE...")

    # ===== Anime Rating Triggers =====

    # INSERT trigger
    db.execute_update("""
        CREATE TRIGGER trg_anime_rating_insert
        AFTER INSERT ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
                created_at, updated_at
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
                COALESCE(r.is_spoiler, 0),
                NEW.created_at,
                NEW.updated_at
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_anime_rating_insert")

    # UPDATE trigger
    db.execute_update("""
        CREATE TRIGGER trg_anime_rating_update
        AFTER UPDATE ON user_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
                created_at, updated_at
            )
            SELECT
                'anime_rating',
                NEW.user_id,
                NEW.anime_id,
                COALESCE(r.created_at, OLD.created_at, NEW.updated_at),
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
                COALESCE(r.is_spoiler, 0),
                OLD.created_at,
                NEW.updated_at
            FROM users u
            JOIN anime a ON a.id = NEW.anime_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN user_reviews r ON r.user_id = NEW.user_id AND r.anime_id = NEW.anime_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_anime_rating_update")

    # DELETE trigger
    db.execute_update("""
        CREATE TRIGGER trg_anime_rating_delete
        AFTER DELETE ON user_ratings
        BEGIN
            DELETE FROM activities
            WHERE activity_type = 'anime_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.anime_id;
        END
    """)
    print("✓ Created trg_anime_rating_delete")

    # ===== Character Rating Triggers =====

    # INSERT trigger
    db.execute_update("""
        CREATE TRIGGER trg_character_rating_insert
        AFTER INSERT ON character_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
                anime_id, anime_title, anime_title_korean,
                created_at, updated_at
            )
            SELECT
                'character_rating',
                NEW.user_id,
                NEW.character_id,
                COALESCE(r.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                c.name_full,
                c.name_korean,
                COALESCE('/' || c.image_local, c.image_url),
                NEW.rating,
                r.title,
                r.content,
                COALESCE(r.is_spoiler, 0),
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
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                NEW.created_at,
                NEW.updated_at
            FROM users u
            JOIN character c ON c.id = NEW.character_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN character_reviews r ON r.user_id = NEW.user_id AND r.character_id = NEW.character_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_character_rating_insert")

    # UPDATE trigger
    db.execute_update("""
        CREATE TRIGGER trg_character_rating_update
        AFTER UPDATE ON character_ratings
        WHEN NEW.status = 'RATED' AND NEW.rating IS NOT NULL
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
                anime_id, anime_title, anime_title_korean,
                created_at, updated_at
            )
            SELECT
                'character_rating',
                NEW.user_id,
                NEW.character_id,
                COALESCE(r.created_at, OLD.created_at, NEW.updated_at),
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                c.name_full,
                c.name_korean,
                COALESCE('/' || c.image_local, c.image_url),
                NEW.rating,
                r.title,
                r.content,
                COALESCE(r.is_spoiler, 0),
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
                 ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                OLD.created_at,
                NEW.updated_at
            FROM users u
            JOIN character c ON c.id = NEW.character_id
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            LEFT JOIN character_reviews r ON r.user_id = NEW.user_id AND r.character_id = NEW.character_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_character_rating_update")

    # DELETE trigger
    db.execute_update("""
        CREATE TRIGGER trg_character_rating_delete
        AFTER DELETE ON character_ratings
        BEGIN
            DELETE FROM activities
            WHERE activity_type = 'character_rating'
              AND user_id = OLD.user_id
              AND item_id = OLD.character_id;
        END
    """)
    print("✓ Created trg_character_rating_delete")

    # ===== User Post Triggers =====

    # INSERT trigger
    db.execute_update("""
        CREATE TRIGGER trg_user_post_insert
        AFTER INSERT ON user_posts
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                review_content,
                created_at, updated_at
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
                NEW.content,
                NEW.created_at,
                NEW.updated_at
            FROM users u
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_user_post_insert")

    # UPDATE trigger
    db.execute_update("""
        CREATE TRIGGER trg_user_post_update
        AFTER UPDATE ON user_posts
        BEGIN
            INSERT OR REPLACE INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                review_content,
                created_at, updated_at
            )
            SELECT
                'user_post',
                NEW.user_id,
                NEW.id,
                OLD.created_at,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0),
                NEW.content,
                OLD.created_at,
                NEW.updated_at
            FROM users u
            LEFT JOIN user_stats us ON u.id = NEW.user_id
            WHERE u.id = NEW.user_id;
        END
    """)
    print("✓ Created trg_user_post_update")

    # DELETE trigger
    db.execute_update("""
        CREATE TRIGGER trg_user_post_delete
        AFTER DELETE ON user_posts
        BEGIN
            DELETE FROM activities
            WHERE activity_type = 'user_post'
              AND user_id = OLD.user_id
              AND item_id = OLD.id;
        END
    """)
    print("✓ Created trg_user_post_delete")

    print("\n=== Trigger fix complete ===")
    print("All triggers now use INSERT OR REPLACE to avoid UNIQUE constraint errors")


if __name__ == "__main__":
    fix_triggers()
