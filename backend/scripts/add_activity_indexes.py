"""Add indexes to activities table for performance"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def add_indexes():
    db = get_db()

    print("Adding indexes to activities table...")

    # Index for activity_time DESC ordering (most important!)
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activities_time
            ON activities(activity_time DESC)
        """)
        print("✓ Created index on activity_time")
    except Exception as e:
        print(f"✗ Error creating activity_time index: {e}")

    # Index for user_id lookups
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activities_user
            ON activities(user_id)
        """)
        print("✓ Created index on user_id")
    except Exception as e:
        print(f"✗ Error creating user_id index: {e}")

    # Index for activity_type filtering
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activities_type
            ON activities(activity_type)
        """)
        print("✓ Created index on activity_type")
    except Exception as e:
        print(f"✗ Error creating activity_type index: {e}")

    # Composite index for type + time
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activities_type_time
            ON activities(activity_type, activity_time DESC)
        """)
        print("✓ Created composite index on activity_type + activity_time")
    except Exception as e:
        print(f"✗ Error creating composite index: {e}")

    # Index for activity_likes.activity_id
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activity_likes_activity
            ON activity_likes(activity_id)
        """)
        print("✓ Created index on activity_likes.activity_id")
    except Exception as e:
        print(f"✗ Error creating activity_likes index: {e}")

    # Index for activity_comments.activity_id
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activity_comments_activity
            ON activity_comments(activity_id)
        """)
        print("✓ Created index on activity_comments.activity_id")
    except Exception as e:
        print(f"✗ Error creating activity_comments index: {e}")

    # Composite index for user likes lookup
    try:
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_activity_likes_user_activity
            ON activity_likes(user_id, activity_id)
        """)
        print("✓ Created composite index on activity_likes(user_id, activity_id)")
    except Exception as e:
        print(f"✗ Error creating user likes index: {e}")

    print("\n✅ Index creation complete!")
    print("\nVerifying indexes...")

    # Show all indexes on activities table
    indexes = db.execute_query("""
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND tbl_name='activities'
        ORDER BY name
    """)

    print(f"\nIndexes on 'activities' table:")
    for idx in indexes:
        print(f"  - {idx[0]}")
        if idx[1]:
            print(f"    {idx[1]}")

if __name__ == "__main__":
    add_indexes()
