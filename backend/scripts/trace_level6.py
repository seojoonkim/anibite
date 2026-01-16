"""
Trace the exact moment when user reached level 6 (550 points)
정확히 550점에 도달한 순간 추적
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

user_id = 4

# Get all activities in chronological order
anime_ratings = db.execute_query(
    '''
    SELECT ur.updated_at as time, 'anime_rating' as type, a.title_romaji as title, a.title_korean as title_kr
    FROM user_ratings ur
    JOIN anime a ON ur.anime_id = a.id
    WHERE ur.user_id = ? AND ur.status = 'RATED'
    ORDER BY ur.updated_at ASC
    ''',
    (user_id,)
)

character_ratings = db.execute_query(
    '''
    SELECT cr.updated_at as time, 'character_rating' as type, c.name_full as title, c.name_native as title_kr
    FROM character_ratings cr
    JOIN character c ON cr.character_id = c.id
    WHERE cr.user_id = ?
    ORDER BY cr.updated_at ASC
    ''',
    (user_id,)
)

anime_reviews = db.execute_query(
    '''
    SELECT r.created_at as time, 'anime_review' as type, a.title_romaji as title, a.title_korean as title_kr
    FROM user_reviews r
    JOIN anime a ON r.anime_id = a.id
    WHERE r.user_id = ?
    ORDER BY r.created_at ASC
    ''',
    (user_id,)
)

character_reviews = db.execute_query(
    '''
    SELECT cr.created_at as time, 'character_review' as type, c.name_full as title, c.name_native as title_kr
    FROM character_reviews cr
    JOIN character c ON cr.character_id = c.id
    WHERE cr.user_id = ?
    ORDER BY cr.created_at ASC
    ''',
    (user_id,)
)

# Merge and sort all activities
activities = sorted(
    list(anime_ratings) + list(character_ratings) + list(anime_reviews) + list(character_reviews),
    key=lambda x: x[0]
)

# Calculate cumulative score
cumulative_anime = 0
cumulative_char = 0
cumulative_reviews = 0

print("Tracing activities until reaching 550 points (Level 6)...")
print()

for activity in activities:
    time, type_, title, title_kr = activity

    # Update counts
    if type_ == 'anime_rating':
        cumulative_anime += 1
    elif type_ == 'character_rating':
        cumulative_char += 1
    elif type_ in ['anime_review', 'character_review']:
        cumulative_reviews += 1

    score = cumulative_anime * 2 + cumulative_char * 1 + cumulative_reviews * 5

    # Show activities around 550 points
    if 540 <= score <= 560:
        print(f"{time} | Score: {score:3d} | {type_:20s} | {title} ({title_kr})")

        if score == 550:
            print()
            print(f"🎊 LEVEL 6 REACHED at {time}")
            print(f"   Activity: {type_}")
            print(f"   Title: {title} ({title_kr})")
            print(f"   Score: {score} (Anime: {cumulative_anime}×2 + Char: {cumulative_char}×1 + Reviews: {cumulative_reviews}×5)")
            print()

        if score > 550:
            break

print()
print("Current stats:")
print(f"  Anime ratings: {cumulative_anime}")
print(f"  Character ratings: {cumulative_char}")
print(f"  Total reviews: {cumulative_reviews}")
print(f"  Final score: {score}")
