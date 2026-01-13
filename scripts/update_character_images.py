#!/usr/bin/env python3
"""
Update character images in production database
Updates Tenma (198) and Yakumo (202) to use R2 paths
"""
import sqlite3
import sys
from pathlib import Path

# Database path
db_path = Path(__file__).parent.parent / "data" / "anime.db"

if not db_path.exists():
    print(f"Error: Database not found at {db_path}")
    sys.exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Update Tenma
    cursor.execute("UPDATE character SET image_url = ? WHERE id = ?",
                   ('/images/characters/198.jpg', 198))
    print(f"Updated Tenma (198): {cursor.rowcount} rows affected")

    # Update Yakumo
    cursor.execute("UPDATE character SET image_url = ? WHERE id = ?",
                   ('/images/characters/202.jpg', 202))
    print(f"Updated Yakumo (202): {cursor.rowcount} rows affected")

    # Commit changes
    conn.commit()

    # Verify updates
    cursor.execute("SELECT id, name_full, image_url FROM character WHERE id IN (198, 202)")
    results = cursor.fetchall()

    print("\nVerification:")
    for row in results:
        print(f"  ID {row[0]}: {row[1]} -> {row[2]}")

    conn.close()
    print("\nSuccess!")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
