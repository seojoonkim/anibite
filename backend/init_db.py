"""
Initialize database with schema
Creates all tables needed for AniPass
"""
import sqlite3
import os
from pathlib import Path

# Database path
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "anime.db"

print(f"Initializing database at: {DB_PATH}")

# Connect to database
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Read and execute schema
schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
if schema_path.exists():
    print(f"Reading schema from: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()

    # Execute schema
    cursor.executescript(schema)
    print("✅ Schema created successfully!")
else:
    print(f"⚠️ Schema file not found at: {schema_path}")
    # Create minimal schema for user authentication
    print("Creating minimal schema...")

    cursor.executescript("""
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT,
        bio TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Anime table (minimal)
    CREATE TABLE IF NOT EXISTS anime (
        id INTEGER PRIMARY KEY,
        title_romaji TEXT,
        title_english TEXT,
        title_native TEXT,
        type TEXT,
        format TEXT,
        status TEXT,
        description TEXT,
        cover_image_url TEXT,
        average_score INTEGER,
        popularity INTEGER
    );

    -- Ratings table
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
        UNIQUE(user_id, anime_id)
    );

    -- Reviews table
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        rating REAL,
        likes_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
    );

    -- Comments table
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        parent_comment_id INTEGER,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE CASCADE
    );

    -- Follows table
    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER NOT NULL,
        following_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (follower_id, following_id),
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    print("✅ Minimal schema created successfully!")

conn.commit()
conn.close()

print("✅ Database initialization complete!")
print(f"Database file size: {DB_PATH.stat().st_size} bytes")

# Fix triggers to use INSERT OR REPLACE
print("\n🔧 Fixing database triggers...")
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from scripts.fix_railway_triggers import fix_triggers
    fix_triggers()
    print("✅ Triggers fixed successfully!")
except Exception as e:
    print(f"⚠️ Failed to fix triggers: {e}")
    print("Triggers will be fixed on first API call.")
