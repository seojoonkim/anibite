"""
Add preferred_language column to users table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def add_preferred_language_column():
    """Add preferred_language column to users table"""

    print("Adding preferred_language column to users table...")

    try:
        # Check if column already exists
        rows = db.execute_query("PRAGMA table_info(users)")
        columns = [row[1] for row in rows]

        if 'preferred_language' in columns:
            print("✓ preferred_language column already exists")
            return

        # Add column
        db.execute_update(
            "ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'ko'"
        )

        print("✓ Successfully added preferred_language column")
        print("  Default value: 'ko' (Korean)")

    except Exception as e:
        print(f"✗ Failed to add column: {e}")
        raise


if __name__ == "__main__":
    add_preferred_language_column()
