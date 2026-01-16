"""
Fix rank promotion timestamps
승급 메시지의 activity_time을 승급을 트리거한 활동의 시각으로 수정

방법:
1. 사용자의 모든 평점/캐릭터 활동을 시간순으로 조회
2. 누적 점수를 계산하면서 각 승급 점수에 도달하는 시점을 찾기
3. 해당 시점의 activity_time을 승급 메시지에 설정
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
import json


def calculate_score_thresholds():
    """승급 점수 임계값 계산"""
    thresholds = {
        50: (1, 2, "루키", "헌터"),    # Lv.1 -> Lv.2
        120: (2, 3, "헌터", "워리어"),  # Lv.2 -> Lv.3
        220: (3, 4, "워리어", "나이트"), # Lv.3 -> Lv.4
        350: (4, 5, "나이트", "마스터"), # Lv.4 -> Lv.5
        550: (5, 6, "마스터", "하이마스터"), # Lv.5 -> Lv.6
        800: (6, 7, "하이마스터", "그랜드마스터"), # Lv.6 -> Lv.7
        1100: (7, 8, "그랜드마스터", "오타쿠"), # Lv.7 -> Lv.8
        1450: (8, 9, "오타쿠", "오타쿠 킹"), # Lv.8 -> Lv.9
        1800: (9, 10, "오타쿠 킹", "오타쿠 갓"), # Lv.9 -> Lv.10
    }
    return thresholds


def fix_rank_promotion_timestamps():
    """기존 승급 메시지들의 타임스탬프 수정"""

    # 승급 메시지들을 사용자별로 그룹화
    promotions = db.execute_query(
        """
        SELECT
            id, user_id, activity_time, metadata
        FROM activities
        WHERE activity_type = 'rank_promotion'
        ORDER BY user_id, id
        """,
        ()
    )

    print(f"Found {len(promotions)} rank promotions to fix")

    # 사용자별로 처리
    users = set([p[1] for p in promotions])

    for user_id in users:
        print(f"\n=== Processing User {user_id} ===")

        # 해당 사용자의 승급 메시지들
        user_promotions = [p for p in promotions if p[1] == user_id]

        # 승급 메시지를 otaku_score로 정렬
        user_promotions_with_score = []
        for promo in user_promotions:
            promo_id, _, activity_time, metadata = promo
            try:
                meta_dict = json.loads(metadata)
                otaku_score = meta_dict.get('otaku_score', 0)
                old_level = meta_dict.get('old_level', 0)
                new_level = meta_dict.get('new_level', 0)
                user_promotions_with_score.append({
                    'id': promo_id,
                    'score': otaku_score,
                    'old_level': old_level,
                    'new_level': new_level,
                    'current_time': activity_time
                })
            except:
                print(f"  [WARNING] Failed to parse metadata for promotion {promo_id}")
                continue

        # otaku_score로 정렬
        user_promotions_with_score.sort(key=lambda x: x['score'])

        # 해당 사용자의 모든 활동을 시간순으로 조회
        # activities 테이블이 불완전할 수 있으므로 원본 테이블에서 직접 조회
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

        # 애니메이션 리뷰도 조회
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

        # 캐릭터 리뷰도 조회
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
            key=lambda x: x[0]  # activity_time으로 정렬
        )

        print(f"Found {len(activities)} activities for user {user_id} ({len(anime_ratings)} anime ratings, {len(character_ratings)} char ratings, {len(anime_reviews)} anime reviews, {len(character_reviews)} char reviews)")

        # 누적 점수 계산하면서 승급 시점 찾기
        cumulative_anime_ratings = 0
        cumulative_character_ratings = 0
        cumulative_reviews = 0

        promotion_times = {}  # {score: activity_time}

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
            for promo in user_promotions_with_score:
                target_score = promo['score']
                promo_id = promo['id']

                # 이 승급 점수에 처음 도달한 시점 기록
                if current_score >= target_score and target_score not in promotion_times:
                    promotion_times[target_score] = activity_time
                    print(f"  Score {target_score} reached at {activity_time} with {activity_type}: '{item_title}' (anime={cumulative_anime_ratings}, char={cumulative_character_ratings}, reviews={cumulative_reviews})")

        # 승급 메시지 업데이트
        for promo in user_promotions_with_score:
            promo_id = promo['id']
            target_score = promo['score']
            old_level = promo['old_level']
            new_level = promo['new_level']
            current_time = promo['current_time']

            if target_score in promotion_times:
                correct_time = promotion_times[target_score]

                print(f"\nPromotion {promo_id}: Level {old_level}→{new_level}, Score {target_score}")
                print(f"  Current time: {current_time}")
                print(f"  Correct time: {correct_time}")

                # 업데이트
                db.execute_update(
                    """
                    UPDATE activities
                    SET activity_time = ?
                    WHERE id = ?
                    """,
                    (correct_time, promo_id)
                )

                print(f"  ✓ Updated!")
            else:
                print(f"\n[WARNING] Could not find activity time for promotion {promo_id} (score {target_score})")

    print("\n\n✓ All rank promotion timestamps have been fixed!")


if __name__ == "__main__":
    fix_rank_promotion_timestamps()
