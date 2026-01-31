"""Database migration: Add OAuth support"""
import sqlite3
from pathlib import Path

def add_oauth_support():
    db_path = Path(__file__).parent.parent.parent / "data" / "anime.db"
    print(f"🔍 Database path: {db_path}")
    print(f"🔍 Database exists: {db_path.exists()}")
    print(f"🔍 Database size: {db_path.stat().st_size if db_path.exists() else 0} bytes")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"🔍 Current columns: {', '.join(column_names)}")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT NULL")
        print("✅ Added oauth_provider column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  oauth_provider column already exists")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_id TEXT NULL")
        print("✅ Added oauth_id column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  oauth_id column already exists")
        else:
            raise

    try:
        cursor.execute("""
            CREATE UNIQUE INDEX idx_oauth_user
            ON users(oauth_provider, oauth_id)
            WHERE oauth_provider IS NOT NULL AND oauth_provider != 'local'
        """)
        print("✅ Created unique index for OAuth users")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower():
            print("⚠️  Index already exists")
        else:
            raise

    cursor.execute("""
        UPDATE users
        SET oauth_provider = 'local'
        WHERE oauth_provider IS NULL
    """)
    updated = cursor.rowcount
    print(f"✅ Marked {updated} existing users as 'local'")

    conn.commit()
    conn.close()
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    add_oauth_support()
