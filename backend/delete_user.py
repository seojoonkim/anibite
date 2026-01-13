"""
Delete a user by email or username
"""
import sqlite3
import sys
from pathlib import Path

# Database path
DATA_DIR = Path("/app/data")
DB_PATH = DATA_DIR / "anime.db"

# For local testing
if not DB_PATH.exists():
    DB_PATH = Path("data/anime.db")

def delete_user(identifier):
    """Delete user by email or username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find user
    cursor.execute(
        "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    )
    user = cursor.fetchone()

    if not user:
        print(f"❌ User not found: {identifier}")
        conn.close()
        return

    user_id, username, email = user
    print(f"Found user: {username} ({email})")

    # Delete related data first (to avoid foreign key constraints)
    tables_to_clean = [
        'user_stats',
        'ratings',
        'reviews',
        'character_reviews',
        'comments',
        'review_comments',
        'character_review_comments',
        'user_posts',
        'follows',
        'user_activity',
        'notifications'
    ]

    for table in tables_to_clean:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"  - Deleted {deleted} records from {table}")
        except sqlite3.Error as e:
            # Table might not exist or have user_id column
            pass

    # Delete user
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    print(f"✅ User deleted successfully: {username} ({email})")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_user.py <email_or_username>")
        print("Example: python delete_user.py simon@hashed.com")
        sys.exit(1)

    identifier = sys.argv[1]
    delete_user(identifier)
