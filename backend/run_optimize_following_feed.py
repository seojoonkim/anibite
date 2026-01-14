#!/usr/bin/env python3
"""
Apply database optimizations for following feed performance
"""
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_path

def optimize_following_feed():
    """Apply indexes and optimizations for following feed"""

    db_path = get_db_path()
    print(f"Optimizing database: {db_path}")

    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'optimize_following_feed.sql')
    with open(sql_file, 'r') as f:
        sql = f.read()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute all statements
        cursor.executescript(sql)
        conn.commit()
        print("✓ Indexes created successfully")

        # Show index info
        cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='index'
            AND name LIKE 'idx_%'
            ORDER BY name
        """)

        indexes = cursor.fetchall()
        print(f"\n✓ Total indexes: {len(indexes)}")
        for idx_name, idx_sql in indexes:
            if idx_sql:  # Some system indexes don't have SQL
                print(f"  - {idx_name}")

        print("\n✓ Database optimization complete!")

    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True

if __name__ == '__main__':
    success = optimize_following_feed()
    sys.exit(0 if success else 1)
