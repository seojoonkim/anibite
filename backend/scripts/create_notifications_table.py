"""Create notifications table for efficient notification management"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def create_notifications_table():
    db = get_db()

    # Create notifications table
    print("Creating notifications table...")
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            actor_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            activity_id INTEGER,
            comment_id INTEGER,
            content TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for faster lookups
    print("Creating indexes...")
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_created
        ON notifications(user_id, created_at DESC)
    """)

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_notifications_activity
        ON notifications(activity_id, actor_id, type)
    """)

    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_notifications_unread
        ON notifications(user_id, is_read, created_at DESC)
    """)

    print("✅ Notifications table created successfully")
    print("   - user_id: User receiving the notification")
    print("   - actor_id: User who performed the action")
    print("   - type: 'like' or 'comment'")
    print("   - activity_id: Related activity")
    print("   - comment_id: Comment ID (for comment notifications)")
    print("   - content: Comment text (for comment notifications)")
    print("   - is_read: Read status")
    print("   - created_at: Timestamp")

if __name__ == "__main__":
    create_notifications_table()
