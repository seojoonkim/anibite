"""
Download anime.db from temporary hosting
Run this once to populate the Railway volume with the full database
"""
import os
import urllib.request
from pathlib import Path

# Database path
DATA_DIR = Path("/app/data")
DB_PATH = DATA_DIR / "anime.db"

# Download URL from environment variable or fallback to localtunnel
DOWNLOAD_URL = os.getenv("DB_DOWNLOAD_URL", "https://github.com/seojoonkim/anipass/releases/download/v1.0.0-db/anime.db")

print(f"Downloading database from: {DOWNLOAD_URL}")
print(f"Target location: {DB_PATH}")

# Create directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Download the file
try:
    print("Starting download...")
    urllib.request.urlretrieve(DOWNLOAD_URL, str(DB_PATH))

    # Check file size
    file_size = DB_PATH.stat().st_size
    print(f"✅ Download complete!")
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")

except Exception as e:
    print(f"❌ Download failed: {e}")
    exit(1)

# Backfill Japanese titles in activities table
print("\n🌐 Backfilling Japanese titles in activities table...")
try:
    import sqlite3

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(activities)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'anime_title_native' not in column_names:
        print("  Adding anime_title_native column...")
        cursor.execute("ALTER TABLE activities ADD COLUMN anime_title_native TEXT")

    if 'item_title_native' not in column_names:
        print("  Adding item_title_native column...")
        cursor.execute("ALTER TABLE activities ADD COLUMN item_title_native TEXT")

    # Backfill anime native titles for character activities
    cursor.execute("""
        UPDATE activities
        SET anime_title_native = (
            SELECT a.title_native
            FROM anime a
            WHERE a.id = activities.anime_id
        )
        WHERE activity_type IN ('character_rating', 'character_review')
        AND anime_id IS NOT NULL
        AND anime_title_native IS NULL
    """)
    anime_count = cursor.rowcount

    # Backfill character native names
    cursor.execute("""
        UPDATE activities
        SET item_title_native = (
            SELECT c.name_native
            FROM character c
            WHERE c.id = activities.item_id
        )
        WHERE activity_type IN ('character_rating', 'character_review')
        AND item_id IS NOT NULL
        AND item_title_native IS NULL
    """)
    char_count = cursor.rowcount

    # Backfill anime native titles for anime activities
    cursor.execute("""
        UPDATE activities
        SET item_title_native = (
            SELECT a.title_native
            FROM anime a
            WHERE a.id = activities.item_id
        )
        WHERE activity_type IN ('anime_rating', 'anime_review')
        AND item_id IS NOT NULL
        AND item_title_native IS NULL
    """)
    anime_item_count = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Backfilled {anime_count} anime titles, {char_count} character names, and {anime_item_count} anime items!")

except Exception as e:
    print(f"⚠️ Backfill failed: {e}")
    print("Application will continue but Japanese titles may not display correctly.")
