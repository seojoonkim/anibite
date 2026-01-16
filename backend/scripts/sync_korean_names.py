#!/usr/bin/env python3
"""
Sync Korean names from JSON file to database
This script runs on startup if korean_names.json exists
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

def sync_korean_names():
    """Sync Korean names from JSON file to database"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'korean_names.json')

    if not os.path.exists(json_path):
        print(f"Korean names JSON not found at {json_path}")
        return 0

    # Check if we already have Korean names in DB
    result = db.execute_query(
        "SELECT COUNT(*) as cnt FROM character WHERE name_korean IS NOT NULL AND name_korean != ''"
    )
    existing_count = result[0]['cnt'] if result else 0

    if existing_count > 1000:
        print(f"Already have {existing_count} Korean names in DB, skipping sync")
        return existing_count

    print(f"Loading Korean names from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        korean_names = json.load(f)

    print(f"Syncing {len(korean_names)} Korean names to database...")

    # Batch update for performance
    batch_size = 1000
    items = list(korean_names.items())
    count = 0

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        for char_id, korean_name in batch:
            try:
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, int(char_id))
                )
                count += 1
            except Exception as e:
                print(f"Error updating character {char_id}: {e}")

        if (i + batch_size) % 10000 == 0:
            print(f"Progress: {min(i + batch_size, len(items))}/{len(items)}")

    print(f"✓ Synced {count} Korean names")
    return count

if __name__ == "__main__":
    sync_korean_names()
