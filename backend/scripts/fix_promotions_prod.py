"""
Fix rank promotions in production database
프로덕션 DB의 승급 메시지를 올바른 시각으로 재생성
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
import json


def get_rank_info(otaku_score):
    """Get rank name and level from otaku score"""
    if otaku_score < 50:
        return "루키", 1
    elif otaku_score < 120:
        return "헌터", 2
    elif otaku_score < 220:
        return "워리어", 3
    elif otaku_score < 350:
        return "나이트", 4
    elif otaku_score < 550:
        return "마스터", 5
    elif otaku_score < 800:
        return "하이마스터", 6
    elif otaku_score < 1100:
        return "그랜드마스터", 7
    elif otaku_score < 1450:
        return "오타쿠", 8
    elif otaku_score < 1800:
        return "오타쿠 킹", 9
    else:
        return "오타쿠 갓", 10


def fix_rank_promotions(user_id):
    """Fix rank promotions for a user based on their actual activities"""

    print(f"\n=== Fixing rank promotions for user {user_id} ===\n")

    # Check current stats
    stats = db.execute_query(
        'SELECT total_rated, total_character_ratings, total_reviews, otaku_score FROM user_stats WHERE user_id = ?',
        (user_id,),
        fetch_one=True
    )

    print(f"Current stats from user_stats table:")
    print(f"  Anime ratings: {stats[0]}")
    print(f"  Character ratings: {stats[1]}")
    print(f"  Total reviews: {stats[2]}")
    print(f"  Otaku score: {stats[3]}")

    # Delete existing promotions
    db.execute_update(
        'DELETE FROM activities WHERE user_id = ? AND activity_type = "rank_promotion"',
        (user_id,)
    )
    print(f"\n✓ Deleted existing rank promotions")

    # Get user info
    user_info = db.execute_query(
        'SELECT username, display_name, avatar_url FROM users WHERE id = ?',
        (user_id,),
        fetch_one=True
    )

    if not user_info:
        print(f"ERROR: User {user_id} not found!")
        return

    username, display_name, avatar_url = user_info[0], user_info[1], user_info[2]

    # Get all activities in chronological order
    anime_ratings = db.execute_query(
        '''
        SELECT ur.updated_at as activity_time, 'anime_rating' as activity_type, a.title_romaji as item_title
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        ORDER BY ur.updated_at ASC
        ''',
        (user_id,)
    )

    character_ratings = db.execute_query(
        '''
        SELECT cr.updated_at as activity_time, 'character_rating' as activity_type, c.name_full as item_title
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
        ORDER BY cr.updated_at ASC
        ''',
        (user_id,)
    )

    anime_reviews = db.execute_query(
        '''
        SELECT r.created_at as activity_time, 'anime_review' as activity_type, a.title_romaji as item_title
        FROM user_reviews r
        JOIN anime a ON r.anime_id = a.id
        WHERE r.user_id = ?
        ORDER BY r.created_at ASC
        ''',
        (user_id,)
    )

    character_reviews = db.execute_query(
        '''
        SELECT cr.created_at as activity_time, 'character_review' as activity_type, c.name_full as item_title
        FROM character_reviews cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
        ORDER BY cr.created_at ASC
        ''',
        (user_id,)
    )

    # Merge and sort
    activities = sorted(
        list(anime_ratings) + list(character_ratings) + list(anime_reviews) + list(character_reviews),
        key=lambda x: x[0]
    )

    print(f"\n✓ Found {len(activities)} total activities")
    print(f"  - Anime ratings: {len(anime_ratings)}")
    print(f"  - Character ratings: {len(character_ratings)}")
    print(f"  - Anime reviews: {len(anime_reviews)}")
    print(f"  - Character reviews: {len(character_reviews)}")

    # Calculate cumulative score and generate promotions
    cumulative_anime = 0
    cumulative_char = 0
    cumulative_reviews = 0

    thresholds = [50, 120, 220, 350, 550, 800, 1100, 1450, 1800]
    generated = set()

    print(f"\nGenerating rank promotions...")

    for activity in activities:
        activity_time, activity_type, item_title = activity

        if activity_type == 'anime_rating':
            cumulative_anime += 1
        elif activity_type == 'character_rating':
            cumulative_char += 1
        elif activity_type in ['anime_review', 'character_review']:
            cumulative_reviews += 1

        current_score = (cumulative_anime * 2) + (cumulative_char * 1) + (cumulative_reviews * 5)

        for threshold in thresholds:
            if current_score >= threshold and threshold not in generated:
                old_rank, old_level = get_rank_info(threshold - 1)
                new_rank, new_level = get_rank_info(threshold)

                print(f"\n  Lv.{old_level} {old_rank} → Lv.{new_level} {new_rank}")
                print(f"    Score {threshold} reached at: {activity_time}")
                print(f"    Activity: {activity_type} - {item_title}")

                metadata = json.dumps({
                    "old_rank": old_rank,
                    "old_level": old_level,
                    "new_rank": new_rank,
                    "new_level": new_level,
                    "otaku_score": current_score
                })

                db.execute_insert(
                    '''
                    INSERT INTO activities (
                        activity_type, user_id, username, display_name, avatar_url,
                        item_id, metadata, activity_time, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''',
                    (
                        'rank_promotion',
                        user_id,
                        username,
                        display_name,
                        avatar_url,
                        None,
                        metadata,
                        activity_time
                    )
                )

                generated.add(threshold)

    print(f"\n✓ Generated {len(generated)} rank promotions!")

    # Show final rank
    current_rank, current_level = get_rank_info(stats[3])
    print(f"✓ Current rank: Lv.{current_level} {current_rank} ({stats[3]} points)")


if __name__ == "__main__":
    # Fix for user 4 (simon)
    fix_rank_promotions(4)
    print("\n✅ Done!")
