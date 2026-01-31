"""Force add OAuth columns to database"""
import sqlite3
from pathlib import Path

# Use absolute path for Railway
db_path = Path("/app/data/anime.db") if Path("/app/data").exists() else Path(__file__).parent.parent.parent / "data" / "anime.db"

print(f"🔍 Database path: {db_path}")
print(f"🔍 Database exists: {db_path.exists()}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check current schema
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"🔍 Current columns: {', '.join(columns)}")

    if 'oauth_provider' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT")
        print("✅ Added oauth_provider column")
    else:
        print("⚠️  oauth_provider already exists")

    if 'oauth_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_id TEXT")
        print("✅ Added oauth_id column")
    else:
        print("⚠️  oauth_id already exists")

    # Try to create index
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX idx_oauth_user
            ON users(oauth_provider, oauth_id)
            WHERE oauth_provider IS NOT NULL AND oauth_provider != 'local'
        """)
        print("✅ Created unique index")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower():
            print("⚠️  Index already exists")
        else:
            raise

    # Mark existing users as local
    cursor.execute("UPDATE users SET oauth_provider = 'local' WHERE oauth_provider IS NULL")
    updated = cursor.rowcount
    print(f"✅ Marked {updated} users as 'local'")

    conn.commit()
    print("\n✅ Migration completed successfully!")

    # Verify
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\n✅ Final columns: {', '.join(columns)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    raise
finally:
    conn.close()
