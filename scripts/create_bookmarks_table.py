"""Create bookmarks table for saved activities"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def create_bookmarks_table():
    db = get_db()

    # Create bookmarks table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            activity_user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, activity_type, activity_user_id, item_id)
        )
    """)

    # Create index for faster lookups
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user
        ON bookmarks(user_id, created_at DESC)
    """)

    print("✅ Bookmarks table created successfully")
    print("   - user_id: The user who bookmarked")
    print("   - activity_type: Type of activity (anime_rating, character_rating, user_post)")
    print("   - activity_user_id: The user who created the activity")
    print("   - item_id: The ID of the item (anime_id, character_id, post_id)")
    print("   - created_at: When the bookmark was created")

if __name__ == "__main__":
    create_bookmarks_table()
