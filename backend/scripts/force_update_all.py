"""
Force update user stats and regenerate rank promotions
통계를 강제로 업데이트하고 승급 메시지를 재생성
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


def force_update_user(user_id):
    """특정 사용자의 통계를 강제로 업데이트하고 승급 메시지 재생성"""

    print(f"=== Force updating user {user_id} ===\n")

    # Step 1: Calculate correct stats
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

    total_reviews = anime_review_count + char_review_count
    correct_score = anime_count * 2 + char_count * 1 + total_reviews * 5

    print(f"Calculated stats:")
    print(f"  Anime ratings: {anime_count}")
    print(f"  Character ratings: {char_count}")
    print(f"  Anime reviews: {anime_review_count}")
    print(f"  Character reviews: {char_review_count}")
    print(f"  Total reviews: {total_reviews}")
    print(f"  Correct score: {correct_score}")
    print()

    # Step 2: Update user_stats
    db.execute_update(
        """
        UPDATE user_stats
        SET total_reviews = ?,
            otaku_score = ?
        WHERE user_id = ?
        """,
        (total_reviews, correct_score, user_id)
    )
    print(f"✓ Updated user_stats")
    print()

    # Step 3: Delete all existing rank promotions
    db.execute_update(
        """
        DELETE FROM activities
        WHERE user_id = ? AND activity_type = 'rank_promotion'
        """,
        (user_id,)
    )
    print("✓ Deleted existing rank promotions\n")

    # Step 4: Get user info
    user_info = db.execute_query(
        "SELECT username, display_name, avatar_url FROM users WHERE id = ?",
        (user_id,),
        fetch_one=True
    )

    if not user_info:
        print(f"User {user_id} not found!")
        return

    username, display_name, avatar_url = user_info[0], user_info[1], user_info[2]

    # Step 5: Get all activities in chronological order
    anime_ratings = db.execute_query(
        """
        SELECT ur.updated_at as activity_time, 'anime_rating' as activity_type, a.title_romaji as item_title
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        ORDER BY ur.updated_at ASC
        """,
        (user_id,)
    )

    character_ratings = db.execute_query(
        """
        SELECT cr.updated_at as activity_time, 'character_rating' as activity_type, c.name_full as item_title
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
        ORDER BY cr.updated_at ASC
        """,
        (user_id,)
    )

    anime_reviews = db.execute_query(
        """
        SELECT r.created_at as activity_time, 'anime_review' as activity_type, a.title_romaji as item_title
        FROM user_reviews r
        JOIN anime a ON r.anime_id = a.id
        WHERE r.user_id = ?
        ORDER BY r.created_at ASC
        """,
        (user_id,)
    )

    character_reviews = db.execute_query(
        """
        SELECT cr.created_at as activity_time, 'character_review' as activity_type, c.name_full as item_title
        FROM character_reviews cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
        ORDER BY cr.created_at ASC
        """,
        (user_id,)
    )

    # Merge and sort all activities
    activities = sorted(
        list(anime_ratings) + list(character_ratings) + list(anime_reviews) + list(character_reviews),
        key=lambda x: x[0]
    )

    print(f"Found {len(activities)} total activities\n")

    # Step 6: Calculate cumulative score and generate promotions
    cumulative_anime_ratings = 0
    cumulative_character_ratings = 0
    cumulative_reviews = 0

    promotion_thresholds = [50, 120, 220, 350, 550, 800, 1100, 1450, 1800]
    generated_promotions = set()

    for activity in activities:
        activity_time, activity_type, item_title = activity

        # Update cumulative counts
        if activity_type == 'anime_rating':
            cumulative_anime_ratings += 1
        elif activity_type == 'character_rating':
            cumulative_character_ratings += 1
        elif activity_type in ['anime_review', 'character_review']:
            cumulative_reviews += 1

        current_score = (cumulative_anime_ratings * 2) + (cumulative_character_ratings * 1) + (cumulative_reviews * 5)

        # Check for promotions
        for threshold in promotion_thresholds:
            if current_score >= threshold and threshold not in generated_promotions:
                old_rank, old_level = get_rank_info(threshold - 1)
                new_rank, new_level = get_rank_info(threshold)

                print(f"Promotion: Lv.{old_level} {old_rank} → Lv.{new_level} {new_rank}")
                print(f"  Score: {threshold} reached at {activity_time}")
                print(f"  Activity: {activity_type} - {item_title}")
                print(f"  Stats: anime={cumulative_anime_ratings}, char={cumulative_character_ratings}, reviews={cumulative_reviews}")

                # Create promotion record
                metadata = json.dumps({
                    "old_rank": old_rank,
                    "old_level": old_level,
                    "new_rank": new_rank,
                    "new_level": new_level,
                    "otaku_score": current_score
                })

                db.execute_insert(
                    """
                    INSERT INTO activities (
                        activity_type, user_id, username, display_name, avatar_url,
                        item_id, metadata, activity_time, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
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

                print(f"  ✓ Generated promotion record\n")
                generated_promotions.add(threshold)

    print(f"\n✓ Generated {len(generated_promotions)} rank promotions!")
    print(f"✓ Final score: {correct_score}")

    current_rank, current_level = get_rank_info(correct_score)
    print(f"✓ Current rank: Lv.{current_level} {current_rank}")


if __name__ == "__main__":
    force_update_user(4)
