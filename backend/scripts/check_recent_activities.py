"""
Check recent activities and current promotion status
최근 활동 및 현재 승급 상태 확인
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from datetime import datetime

user_id = 4

print("=== Current Database Time ===")
db_time = db.execute_query("SELECT datetime('now') as current_time", fetch_one=True)
print(f"Database current time: {db_time['current_time']}")
print()

print("=== Current User Stats ===")
anime_count = db.execute_query(
    "SELECT COUNT(*) as total FROM user_ratings WHERE user_id = ? AND status = 'RATED'",
    (user_id,),
    fetch_one=True
)['total']

char_count = db.execute_query(
    "SELECT COUNT(*) as total FROM character_ratings WHERE user_id = ?",
    (user_id,),
    fetch_one=True
)['total']

anime_review_count = db.execute_query(
    "SELECT COUNT(*) as total FROM user_reviews WHERE user_id = ?",
    (user_id,),
    fetch_one=True
)['total']

char_review_count = db.execute_query(
    "SELECT COUNT(*) as total FROM character_reviews WHERE user_id = ?",
    (user_id,),
    fetch_one=True
)['total']

total_reviews = anime_review_count + char_review_count
score = anime_count * 2 + char_count * 1 + total_reviews * 5

print(f"Anime ratings: {anime_count}")
print(f"Character ratings: {char_count}")
print(f"Anime reviews: {anime_review_count}")
print(f"Character reviews: {char_review_count}")
print(f"Total reviews: {total_reviews}")
print(f"Current score: {score}")
print()

print("=== Last 20 Activities (All Types) ===")
recent_activities = db.execute_query(
    """
    SELECT activity_time, activity_type,
           CASE
               WHEN activity_type = 'anime_rating' THEN (SELECT title_romaji FROM anime WHERE id = anime_id)
               WHEN activity_type = 'character_rating' THEN (SELECT name_full FROM character WHERE id = character_id)
               WHEN activity_type = 'rank_promotion' THEN metadata
               ELSE NULL
           END as title
    FROM activities
    WHERE user_id = ?
    ORDER BY activity_time DESC
    LIMIT 20
    """,
    (user_id,)
)

for act in recent_activities:
    print(f"{act[0]} | {act[1]:20s} | {act[2] if act[2] else ''}")
print()

print("=== All Rank Promotions ===")
promotions = db.execute_query(
    """
    SELECT activity_time, metadata
    FROM activities
    WHERE user_id = ? AND activity_type = 'rank_promotion'
    ORDER BY activity_time ASC
    """,
    (user_id,)
)

for promo in promotions:
    print(f"{promo[0]} | {promo[1]}")
