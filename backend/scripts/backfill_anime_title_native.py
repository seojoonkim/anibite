"""
Backfill anime_title_native field in activities table for character activities
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def backfill_anime_title_native():
    """Backfill anime_title_native for existing character activities"""
    db = get_db()

    print("Backfilling anime_title_native in activities table...")

    # Update character rating/review activities with native anime titles
    db.execute_query(
        """
        UPDATE activities
        SET anime_title_native = (
            SELECT a.title_native
            FROM anime a
            WHERE a.id = activities.anime_id
        )
        WHERE activity_type IN ('character_rating', 'character_review')
        AND anime_id IS NOT NULL
        AND anime_title_native IS NULL
        """
    )

    # Count updated rows
    updated_count = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM activities
        WHERE activity_type IN ('character_rating', 'character_review')
        AND anime_title_native IS NOT NULL
        """,
        fetch_one=True
    )

    print(f"✓ Updated {updated_count['count'] if updated_count else 0} activities with native anime titles")
    print("\nBackfill completed successfully!")

if __name__ == "__main__":
    backfill_anime_title_native()
