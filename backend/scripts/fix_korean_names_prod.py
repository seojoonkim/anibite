"""
Fix character Korean names in PRODUCTION activities table
프로덕션 DB에서 name_native를 name_korean으로 업데이트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Production DB 연결
prod_db_path = os.environ.get('DATABASE_URL', '').replace('sqlite:///', '')
if not prod_db_path or not os.path.exists(prod_db_path):
    print("⚠ Production database not found. Using local database instead.")
    from database import db
else:
    from database import Database
    db = Database(prod_db_path)
    print(f"Using production database: {prod_db_path}")

def fix_korean_names_prod():
    """Update existing data and recreate triggers"""

    print("\n=== Fixing Korean character names in PRODUCTION ===\n")

    # Step 1: Check current data
    print("Step 1: Checking current data...")
    sample_before = db.execute_query("""
        SELECT item_title, item_title_korean
        FROM activities
        WHERE activity_type = 'character_rating'
        LIMIT 3
    """)

    if sample_before:
        print("  Current data (BEFORE):")
        for row in sample_before:
            print(f"    - {row[0]} / {row[1]}")
    print()

    # Step 2: Drop old triggers
    print("Step 2: Dropping old triggers...")
    triggers_to_drop = [
        'trg_character_rating_insert',
        'trg_character_rating_update',
        'trg_character_rating_delete',
        'trg_character_review_insert'
    ]

    for trigger_name in triggers_to_drop:
        try:
            db.execute_query(f"DROP TRIGGER IF EXISTS {trigger_name}")
            print(f"  - Dropped {trigger_name}")
        except Exception as e:
            print(f"  - Error dropping {trigger_name}: {e}")

    print()

    # Step 3: Update existing data
    print("Step 3: Updating existing character rating activities...")
    update_query = """
    UPDATE activities
    SET item_title_korean = (
        SELECT c.name_korean
        FROM character c
        WHERE c.id = activities.item_id
    )
    WHERE activity_type IN ('character_rating', 'character_review')
    AND item_id IS NOT NULL
    """

    try:
        db.execute_query(update_query)
        print("  ✓ Updated character names to use name_korean")
    except Exception as e:
        print(f"  ⚠ Error updating data: {e}")

    print()

    # Step 4: Recreate triggers
    print("Step 4: Recreating triggers with name_korean...")

    # Character rating insert trigger
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
                c.name_korean,
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

    # Character rating update trigger
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
                c.name_korean,
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

    # Character rating delete trigger
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

    # Character review insert trigger
    print("  - Creating trigger: character_review_insert")
    db.execute_query("""
        CREATE TRIGGER IF NOT EXISTS trg_character_review_insert
        AFTER INSERT ON character_reviews
        BEGIN
            UPDATE activities
            SET review_id = NEW.id,
                review_content = NEW.content,
                activity_time = NEW.created_at
            WHERE activity_type = 'character_rating'
              AND user_id = NEW.user_id
              AND item_id = NEW.character_id;

            INSERT INTO activities (
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
                c.name_korean,
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

    print()
    print("✓ All triggers recreated successfully!")
    print()

    # Step 5: Verify changes
    print("Step 5: Verifying changes...")
    sample_after = db.execute_query("""
        SELECT item_title, item_title_korean
        FROM activities
        WHERE activity_type = 'character_rating'
        LIMIT 5
    """)

    if sample_after:
        print("  Current data (AFTER):")
        for row in sample_after:
            print(f"    - {row[0]} / {row[1]}")

    # Count how many were updated
    count = db.execute_query("""
        SELECT COUNT(*)
        FROM activities
        WHERE activity_type IN ('character_rating', 'character_review')
        AND item_title_korean IS NOT NULL
    """, fetch_one=True)

    print()
    print(f"✓ Total character activities with Korean names: {count[0] if count else 0}")
    print()
    print("=== Korean name fix completed! ===")


if __name__ == "__main__":
    try:
        fix_korean_names_prod()
    except Exception as e:
        import traceback
        print(f"\n⚠ Error: {e}")
        print(traceback.format_exc())
