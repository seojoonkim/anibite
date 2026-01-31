"""Check database schema - verify oauth columns exist"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent.parent / "data" / "anime.db"
print(f"Checking database at: {db_path}")
print(f"Database exists: {db_path.exists()}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get users table schema
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("\n=== users table columns ===")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check for oauth columns
oauth_provider_exists = any(col[1] == 'oauth_provider' for col in columns)
oauth_id_exists = any(col[1] == 'oauth_id' for col in columns)

print(f"\noauth_provider column exists: {oauth_provider_exists}")
print(f"oauth_id column exists: {oauth_id_exists}")

conn.close()
