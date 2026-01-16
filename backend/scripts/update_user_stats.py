"""
Update user stats and generate missing rank promotions
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


def update_user_stats(user_id):
    """사용자 통계 업데이트 및 누락된 승급 메시지 생성"""

    # 현재 저장된 otaku_score 조회
    current_stats = db.execute_query(
        "SELECT otaku_score FROM user_stats WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )
    old_otaku_score = current_stats[0] if current_stats else 0

    # 실제 데이터로 점수 재계산
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
    new_otaku_score = anime_count * 2 + char_count * 1 + total_reviews * 5

    print(f"User {user_id} stats:")
    print(f"  Anime ratings: {anime_count}")
    print(f"  Character ratings: {char_count}")
    print(f"  Anime reviews: {anime_review_count}")
    print(f"  Character reviews: {char_review_count}")
    print(f"  Total reviews: {total_reviews}")
    print(f"  Old score: {old_otaku_score}")
    print(f"  New score: {new_otaku_score}")

    # 랭크 비교
    old_rank, old_level = get_rank_info(old_otaku_score)
    new_rank, new_level = get_rank_info(new_otaku_score)

    print(f"  Old rank: {old_rank} (Lv.{old_level})")
    print(f"  New rank: {new_rank} (Lv.{new_level})")

    # user_stats 업데이트
    db.execute_update(
        """
        UPDATE user_stats
        SET otaku_score = ?
        WHERE user_id = ?
        """,
        (new_otaku_score, user_id)
    )

    print(f"  ✓ Updated user_stats")

    # 누락된 승급 메시지 찾기
    if new_level > old_level:
        print(f"\nMissing promotions detected!")

        # 기존 승급 메시지 조회
        existing_promotions = db.execute_query(
            """
            SELECT metadata
            FROM activities
            WHERE user_id = ? AND activity_type = 'rank_promotion'
            ORDER BY id
            """,
            (user_id,)
        )

        existing_levels = set()
        for promo in existing_promotions:
            meta = json.loads(promo[0])
            existing_levels.add(meta['new_level'])

        print(f"  Existing promotion levels: {sorted(existing_levels)}")

        # 누락된 승급 찾기
        for level in range(old_level + 1, new_level + 1):
            if level not in existing_levels:
                print(f"\n  Missing promotion to level {level}")

                # 해당 레벨의 점수 임계값 계산
                thresholds = {
                    2: 50,
                    3: 120,
                    4: 220,
                    5: 350,
                    6: 550,
                    7: 800,
                    8: 1100,
                    9: 1450,
                    10: 1800
                }

                if level in thresholds:
                    target_score = thresholds[level]
                    rank_name, _ = get_rank_info(target_score)
                    prev_rank_name, _ = get_rank_info(target_score - 1)

                    # 해당 점수에 도달한 시점 찾기 (스크립트 실행)
                    print(f"    Need to find activity time for score {target_score}")
                    print(f"    Promotion: {prev_rank_name} (Lv.{level-1}) → {rank_name} (Lv.{level})")

    return new_otaku_score, new_level


if __name__ == "__main__":
    user_id = 4
    update_user_stats(user_id)
