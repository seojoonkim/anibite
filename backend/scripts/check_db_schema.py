#!/usr/bin/env python3
"""Check database schema in production"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH
from database import db

print(f"Database path: {DATABASE_PATH}")
print(f"Database exists: {os.path.exists(DATABASE_PATH)}")

if os.path.exists(DATABASE_PATH):
    print(f"Database size: {os.path.getsize(DATABASE_PATH) / 1024 / 1024:.2f} MB")

try:
    columns = db.execute_query("PRAGMA table_info(activities)")
    col_names = [col['name'] for col in columns]
    print(f"\nActivities table columns ({len(col_names)}):")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

    print(f"\nHas item_year: {'item_year' in col_names}")

    if 'item_year' not in col_names:
        print("\n⚠️  item_year column is MISSING!")
    else:
        print("\n✓ item_year column exists")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
