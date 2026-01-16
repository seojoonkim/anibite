"""
Add metadata column to activities table

This migration adds a metadata TEXT column to store additional data for activities,
especially for rank_promotion activities.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'anime.db')


def add_metadata_column():
    """Add metadata column to activities table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(activities)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'metadata' not in columns:
            print("Adding metadata column to activities table...")
            cursor.execute("ALTER TABLE activities ADD COLUMN metadata TEXT")
            conn.commit()
            print("✅ Successfully added metadata column")
        else:
            print("✅ metadata column already exists")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    add_metadata_column()
