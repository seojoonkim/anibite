"""
Find the exact activity that triggered level 6 promotion
레벨 6 승급을 트리거한 정확한 활동 찾기
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

user_id = 4
target_time = "2026-01-15 17:58:26"

# Find activities around that time
print(f"Looking for activities around {target_time}...")
print()

# Check anime ratings
anime_ratings = db.execute_query(
    '''
    SELECT ur.updated_at, a.title_romaji, a.title_korean, ur.rating
    FROM user_ratings ur
    JOIN anime a ON ur.anime_id = a.id
    WHERE ur.user_id = ?
      AND ur.updated_at BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
    ORDER BY ur.updated_at
    ''',
    (user_id, target_time, target_time)
)

if anime_ratings:
    print("Anime ratings around this time:")
    for r in anime_ratings:
        print(f"  {r[0]}: {r[1]} ({r[2]}) - Rating: {r[3]}")
    print()

# Check character ratings
char_ratings = db.execute_query(
    '''
    SELECT cr.updated_at, c.name_full, c.name_native, cr.rating
    FROM character_ratings cr
    JOIN character c ON cr.character_id = c.id
    WHERE cr.user_id = ?
      AND cr.updated_at BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
    ORDER BY cr.updated_at
    ''',
    (user_id, target_time, target_time)
)

if char_ratings:
    print("Character ratings around this time:")
    for r in char_ratings:
        print(f"  {r[0]}: {r[1]} ({r[2]}) - Rating: {r[3]}")
    print()

# Check anime reviews
anime_reviews = db.execute_query(
    '''
    SELECT r.created_at, a.title_romaji, a.title_korean, substr(r.content, 1, 50)
    FROM user_reviews r
    JOIN anime a ON r.anime_id = a.id
    WHERE r.user_id = ?
      AND r.created_at BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
    ORDER BY r.created_at
    ''',
    (user_id, target_time, target_time)
)

if anime_reviews:
    print("Anime reviews around this time:")
    for r in anime_reviews:
        print(f"  {r[0]}: {r[1]} ({r[2]})")
        print(f"    Content: {r[3]}...")
    print()

# Check character reviews
char_reviews = db.execute_query(
    '''
    SELECT cr.created_at, c.name_full, c.name_native, substr(cr.content, 1, 50)
    FROM character_reviews cr
    JOIN character c ON cr.character_id = c.id
    WHERE cr.user_id = ?
      AND cr.created_at BETWEEN datetime(?, '-5 minutes') AND datetime(?, '+5 minutes')
    ORDER BY cr.created_at
    ''',
    (user_id, target_time, target_time)
)

if char_reviews:
    print("Character reviews around this time:")
    for r in char_reviews:
        print(f"  {r[0]}: {r[1]} ({r[2]})")
        print(f"    Content: {r[3]}...")
    print()

if not (anime_ratings or char_ratings or anime_reviews or char_reviews):
    print("No activities found exactly at this time.")
    print("This timestamp represents when you reached 550 points through cumulative activities.")
