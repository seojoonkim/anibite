"""
Regenerate all rank promotions with correct timestamps
모든 승급 메시지를 삭제하고 올바른 시각으로 다시 생성
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


def regenerate_promotions(user_id):
    """특정 사용자의 모든 승급 메시지를 재생성"""

    print(f"=== Regenerating promotions for User {user_id} ===\n")

    # 1. 기존 승급 메시지 삭제
    db.execute_update(
        """
        DELETE FROM activities
        WHERE user_id = ? AND activity_type = 'rank_promotion'
        """,
        (user_id,)
    )
    print("✓ Deleted existing rank promotions\n")

    # 2. 사용자 정보 조회
    user_info = db.execute_query(
        "SELECT username, display_name, avatar_url FROM users WHERE id = ?",
        (user_id,),
        fetch_one=True
    )

    if not user_info:
        print(f"User {user_id} not found!")
        return

    username, display_name, avatar_url = user_info[0], user_info[1], user_info[2]

    # 3. 모든 활동을 시간순으로 조회 (원본 테이블에서)
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

    # 모든 활동을 합쳐서 시간순 정렬
    activities = sorted(
        list(anime_ratings) + list(character_ratings) + list(anime_reviews) + list(character_reviews),
        key=lambda x: x[0]
    )

    print(f"Found {len(activities)} activities ({len(anime_ratings)} anime, {len(character_ratings)} char, {len(anime_reviews)} anime reviews, {len(character_reviews)} char reviews)\n")

    # 4. 누적 점수를 계산하면서 승급 시점 찾기
    cumulative_anime_ratings = 0
    cumulative_character_ratings = 0
    cumulative_reviews = 0

    promotion_thresholds = [50, 120, 220, 350, 550, 800, 1100, 1450, 1800]
    generated_promotions = set()

    for activity in activities:
        activity_time, activity_type, item_title = activity

        # 점수 계산
        if activity_type == 'anime_rating':
            cumulative_anime_ratings += 1
        elif activity_type == 'character_rating':
            cumulative_character_ratings += 1
        elif activity_type in ['anime_review', 'character_review']:
            cumulative_reviews += 1

        current_score = (cumulative_anime_ratings * 2) + (cumulative_character_ratings * 1) + (cumulative_reviews * 5)

        # 각 승급 점수를 체크
        for threshold in promotion_thresholds:
            if current_score >= threshold and threshold not in generated_promotions:
                old_rank, old_level = get_rank_info(threshold - 1)
                new_rank, new_level = get_rank_info(threshold)

                print(f"Score {threshold} reached at {activity_time}")
                print(f"  with {activity_type}: '{item_title}'")
                print(f"  (anime={cumulative_anime_ratings}, char={cumulative_character_ratings}, reviews={cumulative_reviews})")
                print(f"  Promotion: {old_rank} (Lv.{old_level}) → {new_rank} (Lv.{new_level})")

                # 승급 메시지 생성
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

    print(f"\n✓ Regenerated {len(generated_promotions)} rank promotions!")


if __name__ == "__main__":
    user_id = 4
    regenerate_promotions(user_id)
