"""
Backfill anime_id, anime_title, anime_title_korean for character_rating activities
기존 character_rating activities에 누락된 anime 정보를 채움
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def backfill_character_anime_info():
    """character_rating activities의 anime 정보를 채움"""

    print("Backfilling anime info for character_rating activities...\n")

    # Count activities that need backfilling
    count = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM activities
        WHERE activity_type = 'character_rating'
        AND (anime_id IS NULL OR anime_title IS NULL)
        """,
        fetch_one=True
    )

    total = count['count'] if count else 0
    print(f"Found {total} character_rating activities without anime info")

    if total == 0:
        print("✓ No activities need updating")
        return

    # Update activities with anime info
    db.execute_update("""
        UPDATE activities
        SET
            anime_id = (
                SELECT a.id
                FROM anime a
                JOIN anime_character ac ON a.id = ac.anime_id
                WHERE ac.character_id = activities.item_id
                ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END
                LIMIT 1
            ),
            anime_title = (
                SELECT a.title_romaji
                FROM anime a
                JOIN anime_character ac ON a.id = ac.anime_id
                WHERE ac.character_id = activities.item_id
                ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END
                LIMIT 1
            ),
            anime_title_korean = (
                SELECT a.title_korean
                FROM anime a
                JOIN anime_character ac ON a.id = ac.anime_id
                WHERE ac.character_id = activities.item_id
                ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END
                LIMIT 1
            )
        WHERE activity_type = 'character_rating'
        AND (anime_id IS NULL OR anime_title IS NULL)
    """)

    print(f"✓ Updated {total} activities with anime info")

    # Verify update
    remaining = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM activities
        WHERE activity_type = 'character_rating'
        AND (anime_id IS NULL OR anime_title IS NULL)
        """,
        fetch_one=True
    )

    remaining_count = remaining['count'] if remaining else 0
    if remaining_count > 0:
        print(f"\n⚠ Warning: {remaining_count} activities still missing anime info")
        print("  (These characters may not be associated with any anime)")
    else:
        print("\n✓ All character_rating activities now have anime info")

    # Show sample of updated activities
    print("\nSample updated activities:")
    samples = db.execute_query("""
        SELECT
            item_title as character_name,
            anime_title,
            anime_title_korean
        FROM activities
        WHERE activity_type = 'character_rating'
        AND anime_title IS NOT NULL
        LIMIT 5
    """)

    for sample in samples:
        anime_name = sample['anime_title_korean'] or sample['anime_title']
        print(f"  - {sample['character_name']} → {anime_name}")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Backfilling Character Anime Info")
        print("=" * 60)

        backfill_character_anime_info()

        print("\n" + "=" * 60)
        print("✓ Backfill completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
