"""Check activity_likes table schema"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def check_schema():
    db = get_db()

    print("=== activity_likes table schema ===")
    schema = db.execute_query("PRAGMA table_info(activity_likes)")
    for row in schema:
        print(f"  {row[1]:20} {row[2]:15} NULL={row[3]==0} DEFAULT={row[4]}")

    print("\n=== Sample rows ===")
    samples = db.execute_query("SELECT * FROM activity_likes LIMIT 3")
    if samples:
        for row in samples:
            print(f"  {row}")
    else:
        print("  No data")

if __name__ == "__main__":
    check_schema()
