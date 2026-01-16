"""
Create activity_bookmarks table for server-side bookmark storage
서버 기반 북마크 저장을 위한 테이블 생성
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

print("Creating activity_bookmarks table...")

# Create table
db.execute_update("""
    CREATE TABLE IF NOT EXISTS activity_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, activity_id)
    )
""")

# Create index for faster queries
db.execute_update("""
    CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON activity_bookmarks(user_id)
""")

db.execute_update("""
    CREATE INDEX IF NOT EXISTS idx_bookmarks_activity_id ON activity_bookmarks(activity_id)
""")

print("✅ activity_bookmarks table created successfully!")

# Check table
count = db.execute_query("SELECT COUNT(*) FROM activity_bookmarks", fetch_one=True)
print(f"Current bookmarks count: {count[0]}")
