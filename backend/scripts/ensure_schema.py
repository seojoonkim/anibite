#!/usr/bin/env python3
"""
Ensure database schema is up to date
This script is idempotent and can be run multiple times safely
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

def ensure_item_year_column():
    """Ensure item_year column exists in activities table"""
    try:
        # Check if item_year column exists
        columns = db.execute_query("PRAGMA table_info(activities)")
        col_names = [col['name'] for col in columns]

        if 'item_year' not in col_names:
            print("Adding item_year column to activities table...")
            db.execute_query("ALTER TABLE activities ADD COLUMN item_year INTEGER")
            print("✓ Added item_year column")

            # Populate item_year for anime ratings
            print("Populating item_year for anime ratings...")
            db.execute_query("""
                UPDATE activities
                SET item_year = (
                    SELECT season_year
                    FROM anime
                    WHERE anime.id = activities.item_id
                )
                WHERE activity_type = 'anime_rating'
            """)
            print("✓ Populated item_year column")
        else:
            print("✓ item_year column already exists")

    except Exception as e:
        print(f"Error ensuring item_year column: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Run all schema updates"""
    print("Ensuring database schema is up to date...")
    ensure_item_year_column()
    print("✓ Schema check complete")

if __name__ == "__main__":
    main()
