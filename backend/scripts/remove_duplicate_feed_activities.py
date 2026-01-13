"""
Remove duplicate entries from feed_activities table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def remove_duplicates():
    """Remove duplicate feed activities, keeping the oldest one"""
    db = get_db()

    print("Removing duplicate feed activities...\n")

    # Find duplicates
    duplicates = db.execute_query("""
        SELECT activity_type, user_id, item_id, COUNT(*) as count
        FROM feed_activities
        GROUP BY activity_type, user_id, item_id
        HAVING count > 1
    """)

    if not duplicates:
        print("✓ No duplicates found!")
        return

    print(f"Found {len(duplicates)} duplicate activity combinations")

    total_removed = 0

    for dup in duplicates:
        activity_type, user_id, item_id, count = dup

        # Keep the oldest (smallest id), delete the rest
        db.execute_query("""
            DELETE FROM feed_activities
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM feed_activities
                WHERE activity_type = ? AND user_id = ? AND item_id = ?
            )
            AND activity_type = ? AND user_id = ? AND item_id = ?
        """, (activity_type, user_id, item_id, activity_type, user_id, item_id))

        removed = count - 1
        total_removed += removed
        print(f"  Removed {removed} duplicate(s) for {activity_type} - User {user_id} - Item {item_id}")

    print(f"\n✓ Removed {total_removed} duplicate entries!")

    # Show final count
    result = db.execute_query("SELECT COUNT(*) FROM feed_activities", fetch_one=True)
    total = result[0] if result else 0
    print(f"✓ Total remaining feed_activities: {total}")


def add_unique_constraint():
    """Add unique constraint to prevent future duplicates"""
    db = get_db()

    print("\nAdding unique constraint to feed_activities...")

    try:
        # SQLite doesn't support ADD CONSTRAINT, so we need to check if index exists
        existing_index = db.execute_query("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_feed_unique_activity'
        """, fetch_one=True)

        if existing_index:
            print("✓ Unique constraint already exists")
        else:
            db.execute_query("""
                CREATE UNIQUE INDEX idx_feed_unique_activity
                ON feed_activities(activity_type, user_id, item_id)
            """)
            print("✓ Added unique constraint to prevent duplicates")
    except Exception as e:
        print(f"⚠ Failed to add unique constraint: {e}")


if __name__ == "__main__":
    try:
        print("Cleaning up feed_activities table...\n")
        remove_duplicates()
        add_unique_constraint()
        print("\n✓ Cleanup completed successfully!")
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")
        sys.exit(1)
