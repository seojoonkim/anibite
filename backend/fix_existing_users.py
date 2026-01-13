"""
Fix existing unverified users - set them as verified
"""
import sqlite3
from pathlib import Path

# Database path
DATA_DIR = Path("/app/data")
DB_PATH = DATA_DIR / "anime.db"

# For local testing
if not DB_PATH.exists():
    DB_PATH = Path("data/anime.db")

def fix_unverified_users():
    """Set all unverified users as verified"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find unverified users
    cursor.execute("SELECT id, username, email FROM users WHERE is_verified = 0")
    unverified_users = cursor.fetchall()

    if not unverified_users:
        print("✅ No unverified users found")
        conn.close()
        return

    print(f"Found {len(unverified_users)} unverified users:")
    for user_id, username, email in unverified_users:
        print(f"  - {username} ({email})")

    # Update all unverified users
    cursor.execute("""
        UPDATE users
        SET is_verified = 1,
            verification_token = NULL,
            verification_token_expires = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE is_verified = 0
    """)

    conn.commit()
    updated_count = cursor.rowcount

    print(f"✅ Updated {updated_count} users to verified status")

    conn.close()

if __name__ == "__main__":
    fix_unverified_users()
