"""Check bookmarks in production database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
import os

# Use production database
db_url = os.environ.get('DATABASE_URL')
if db_url:
    print(f"Connecting to production database...")
    db = Database(db_url)
else:
    print("Using local database...")
    from database import get_db
    db = get_db()

# Check bookmarks
try:
    bookmarks = db.execute_query('SELECT * FROM activity_bookmarks ORDER BY created_at DESC LIMIT 10')
    print(f"\nTotal bookmarks found: {len(bookmarks)}")

    if bookmarks:
        print("\nRecent bookmarks:")
        for i, bookmark in enumerate(bookmarks, 1):
            user_id = bookmark[0]
            activity_id = bookmark[1]
            created_at = bookmark[2] if len(bookmark) > 2 else 'N/A'

            # Get user info
            user = db.execute_query(
                "SELECT username FROM users WHERE id = ?",
                (user_id,),
                fetch_one=True
            )
            username = user['username'] if user else 'Unknown'

            # Get activity info
            activity = db.execute_query(
                "SELECT activity_type, item_title FROM activities WHERE id = ?",
                (activity_id,),
                fetch_one=True
            )

            if activity:
                print(f"  {i}. User: {username} (id={user_id})")
                print(f"     Activity: {activity['activity_type']} - {activity['item_title']}")
                print(f"     Activity ID: {activity_id}")
                print(f"     Created: {created_at}")
                print()
    else:
        print("\nNo bookmarks found in database!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
