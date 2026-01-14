"""
Fix activity_likes table structure

This script recreates the activity_likes table with the correct schema.
Old schema had: activity_type, activity_user_id, item_id, user_id
New schema has: activity_id, user_id
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def fix_activity_likes_table():
    """Recreate activity_likes table with correct schema"""
    db = get_db()

    print("=" * 60)
    print("Fixing activity_likes table structure")
    print("=" * 60)

    # Drop old table
    print("\nDropping old activity_likes table...")
    db.execute_query("DROP TABLE IF EXISTS activity_likes")
    print("✓ Dropped old table")

    # Create new table with correct schema
    print("\nCreating new activity_likes table...")
    db.execute_query("""
        CREATE TABLE activity_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(activity_id, user_id),
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✓ Created new table")

    # Create indexes
    print("\nCreating indexes...")
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activity_likes_activity
        ON activity_likes(activity_id)
    """)
    print("  ✓ Created activity_id index")

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_activity_likes_user
        ON activity_likes(user_id)
    """)
    print("  ✓ Created user_id index")

    print("\n" + "=" * 60)
    print("✓ Activity_likes table fixed successfully!")
    print("=" * 60)
    print("\nNew schema:")
    print("  - id (PRIMARY KEY)")
    print("  - activity_id (NOT NULL, references activities.id)")
    print("  - user_id (NOT NULL, references users.id)")
    print("  - created_at (DATETIME)")
    print("  - UNIQUE constraint on (activity_id, user_id)")


if __name__ == "__main__":
    try:
        fix_activity_likes_table()
    except Exception as e:
        print(f"\n✗ Failed to fix table: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
