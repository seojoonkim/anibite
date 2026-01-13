#!/usr/bin/env python3
"""
Update character image paths in database
텐마(198)와 야쿠모(202) 이미지 경로 수정
"""
from database import db

# 경로 수정
characters_to_update = [
    (198, "/images/characters/198.jpg"),
    (202, "/images/characters/202.jpg")
]

print("Updating character image paths...")

for char_id, image_path in characters_to_update:
    db.execute_update(
        "UPDATE character SET image_url = ? WHERE id = ?",
        (image_path, char_id)
    )
    print(f"✓ Updated character {char_id}: {image_path}")

# 확인
print("\nVerifying updates:")
rows = db.execute_query('''
    SELECT id, name_full, image_url
    FROM character
    WHERE id IN (198, 202)
''')

for row in rows:
    print(f"  {row['id']}: {row['name_full']} -> {row['image_url']}")

print("\n✓ Done!")
