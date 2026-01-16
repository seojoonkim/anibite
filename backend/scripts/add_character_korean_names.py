"""
Add name_korean column to character table
캐릭터 테이블에 한국어 이름 컬럼 추가
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def add_character_korean_names():
    """캐릭터 테이블에 name_korean 컬럼 추가"""

    print("=" * 80)
    print("Adding name_korean column to character table...")
    print("=" * 80)

    # Check if column already exists
    columns = db.execute_query("PRAGMA table_info(character)")
    column_names = [col[1] for col in columns]

    if 'name_korean' in column_names:
        print("✓ name_korean column already exists")
    else:
        print("Adding name_korean column...")
        db.execute_update("ALTER TABLE character ADD COLUMN name_korean TEXT")
        print("✓ name_korean column added")

    # Check if index exists
    indices = db.execute_query("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='character'")
    index_names = [idx[0] for idx in indices]

    if 'idx_character_name_korean' in index_names:
        print("✓ idx_character_name_korean index already exists")
    else:
        print("Creating index on name_korean...")
        db.execute_update("CREATE INDEX idx_character_name_korean ON character(name_korean)")
        print("✓ idx_character_name_korean index created")

    print("\n" + "=" * 80)
    print("Migration complete!")
    print("=" * 80)

    # Show statistics
    total = db.execute_query("SELECT COUNT(*) as total FROM character", fetch_one=True)[0]
    with_korean = db.execute_query("SELECT COUNT(*) as total FROM character WHERE name_korean IS NOT NULL", fetch_one=True)[0]

    print(f"\nStatistics:")
    print(f"  Total characters: {total:,}")
    print(f"  With Korean names: {with_korean:,} ({with_korean/total*100:.1f}%)")
    print(f"  Without Korean names: {total-with_korean:,} ({(total-with_korean)/total*100:.1f}%)")
    print()


if __name__ == "__main__":
    add_character_korean_names()
