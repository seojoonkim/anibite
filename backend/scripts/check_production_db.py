"""
Check production database stats
프로덕션 DB의 실제 통계 확인
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

user_id = 4

# 실제 데이터 조회
anime_count = db.execute_query(
    'SELECT COUNT(*) FROM user_ratings WHERE user_id = ? AND status = "RATED"',
    (user_id,),
    fetch_one=True
)[0]

char_count = db.execute_query(
    'SELECT COUNT(*) FROM character_ratings WHERE user_id = ?',
    (user_id,),
    fetch_one=True
)[0]

anime_review_count = db.execute_query(
    'SELECT COUNT(*) FROM user_reviews WHERE user_id = ?',
    (user_id,),
    fetch_one=True
)[0]

char_review_count = db.execute_query(
    'SELECT COUNT(*) FROM character_reviews WHERE user_id = ?',
    (user_id,),
    fetch_one=True
)[0]

# user_stats 테이블 확인
stats = db.execute_query(
    'SELECT total_rated, total_character_ratings, total_reviews, otaku_score FROM user_stats WHERE user_id = ?',
    (user_id,),
    fetch_one=True
)

print(f"Production Database Stats for User {user_id}:")
print(f"\nActual Data:")
print(f"  Anime ratings: {anime_count}")
print(f"  Character ratings: {char_count}")
print(f"  Anime reviews: {anime_review_count}")
print(f"  Character reviews: {char_review_count}")
print(f"  Total reviews: {anime_review_count + char_review_count}")
print(f"  Calculated score: {anime_count * 2 + char_count * 1 + (anime_review_count + char_review_count) * 5}")

print(f"\nuser_stats Table:")
print(f"  total_rated: {stats[0]}")
print(f"  total_character_ratings: {stats[1]}")
print(f"  total_reviews: {stats[2]}")
print(f"  otaku_score: {stats[3]}")

# 승급 메시지 개수
promotion_count = db.execute_query(
    'SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = "rank_promotion"',
    (user_id,),
    fetch_one=True
)[0]

print(f"\nRank Promotions: {promotion_count}")
