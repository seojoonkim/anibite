"""
Activity Like Service
활동 좋아요 관리
"""
from typing import Dict, List
from database import db, dict_from_row


def like_activity(user_id: int, activity_type: str, activity_user_id: int, item_id: int) -> bool:
    """
    활동에 좋아요 추가
    애니메이션/캐릭터 평가는 리뷰가 있으면 review_likes, 없으면 activity_likes 사용
    """
    # 애니메이션 평가/리뷰
    if activity_type in ['anime_rating', 'anime_review']:
        try:
            # 리뷰가 있는지 확인
            review = db.execute_query(
                "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
                (activity_user_id, item_id),
                fetch_one=True
            )

            if review:
                # 리뷰가 있으면 review_likes에 저장
                review_id = review['id']
                db.execute_insert(
                    "INSERT INTO review_likes (user_id, review_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (user_id, review_id)
                )
                db.execute_update(
                    "UPDATE user_reviews SET likes_count = likes_count + 1 WHERE id = ?",
                    (review_id,)
                )
                return True
            else:
                # 리뷰가 없으면 평점이 있는지 확인하고 activity_likes에 저장
                rating = db.execute_query(
                    "SELECT id FROM user_ratings WHERE user_id = ? AND anime_id = ?",
                    (activity_user_id, item_id),
                    fetch_one=True
                )
                if rating:
                    db.execute_insert(
                        "INSERT INTO activity_likes (user_id, activity_type, activity_user_id, item_id) VALUES (?, ?, ?, ?)",
                        (user_id, activity_type, activity_user_id, item_id)
                    )
                    return True
                return False
        except Exception:
            return False

    # 캐릭터 평가/리뷰
    elif activity_type == 'character_rating':
        try:
            # 캐릭터 리뷰가 있는지 확인
            review = db.execute_query(
                "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                (activity_user_id, item_id),
                fetch_one=True
            )

            if review:
                # 리뷰가 있으면 character_review_likes에 저장
                review_id = review['id']
                db.execute_insert(
                    "INSERT INTO character_review_likes (user_id, review_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (user_id, review_id)
                )
                db.execute_update(
                    "UPDATE character_reviews SET likes_count = likes_count + 1 WHERE id = ?",
                    (review_id,)
                )
                return True
            else:
                # 리뷰가 없으면 평점이 있는지 확인하고 activity_likes에 저장
                rating = db.execute_query(
                    "SELECT id FROM character_ratings WHERE user_id = ? AND character_id = ?",
                    (activity_user_id, item_id),
                    fetch_one=True
                )
                if rating:
                    db.execute_insert(
                        "INSERT INTO activity_likes (user_id, activity_type, activity_user_id, item_id) VALUES (?, ?, ?, ?)",
                        (user_id, activity_type, activity_user_id, item_id)
                    )
                    return True
                return False
        except Exception:
            return False

    # 기타 활동은 activity_likes 테이블에 저장
    try:
        db.execute_insert(
            """
            INSERT INTO activity_likes (user_id, activity_type, activity_user_id, item_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, activity_type, activity_user_id, item_id)
        )
        return True
    except Exception:
        return False


def unlike_activity(user_id: int, activity_type: str, activity_user_id: int, item_id: int) -> bool:
    """
    활동 좋아요 취소
    애니메이션/캐릭터 평가는 리뷰가 있으면 review_likes, 없으면 activity_likes에서 삭제
    """
    # 애니메이션 평가/리뷰
    if activity_type in ['anime_rating', 'anime_review']:
        try:
            # 리뷰가 있는지 확인
            review = db.execute_query(
                "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
                (activity_user_id, item_id),
                fetch_one=True
            )

            if review:
                # 리뷰가 있으면 review_likes에서 삭제
                review_id = review['id']
                result = db.execute_update(
                    "DELETE FROM review_likes WHERE user_id = ? AND review_id = ?",
                    (user_id, review_id)
                )
                if result > 0:
                    db.execute_update(
                        "UPDATE user_reviews SET likes_count = CASE WHEN likes_count > 0 THEN likes_count - 1 ELSE 0 END WHERE id = ?",
                        (review_id,)
                    )
                    return True
                return False
            else:
                # 리뷰가 없으면 activity_likes에서 삭제
                result = db.execute_update(
                    "DELETE FROM activity_likes WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?",
                    (user_id, activity_type, activity_user_id, item_id)
                )
                return result > 0
        except Exception:
            return False

    # 캐릭터 평가/리뷰
    elif activity_type == 'character_rating':
        try:
            # 캐릭터 리뷰가 있는지 확인
            review = db.execute_query(
                "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                (activity_user_id, item_id),
                fetch_one=True
            )

            if review:
                # 리뷰가 있으면 character_review_likes에서 삭제
                review_id = review['id']
                result = db.execute_update(
                    "DELETE FROM character_review_likes WHERE user_id = ? AND review_id = ?",
                    (user_id, review_id)
                )
                if result > 0:
                    db.execute_update(
                        "UPDATE character_reviews SET likes_count = CASE WHEN likes_count > 0 THEN likes_count - 1 ELSE 0 END WHERE id = ?",
                        (review_id,)
                    )
                    return True
                return False
            else:
                # 리뷰가 없으면 activity_likes에서 삭제
                result = db.execute_update(
                    "DELETE FROM activity_likes WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?",
                    (user_id, activity_type, activity_user_id, item_id)
                )
                return result > 0
        except Exception:
            return False

    # 기타 활동은 activity_likes 테이블에서 삭제
    try:
        result = db.execute_update(
            """
            DELETE FROM activity_likes
            WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?
            """,
            (user_id, activity_type, activity_user_id, item_id)
        )
        return result > 0
    except Exception:
        return False


def is_activity_liked(user_id: int, activity_type: str, activity_user_id: int, item_id: int) -> bool:
    """
    사용자가 해당 활동에 좋아요를 눌렀는지 확인
    리뷰가 있으면 review_likes, 없으면 activity_likes 확인
    """
    # 애니메이션 평가/리뷰
    if activity_type in ['anime_rating', 'anime_review']:
        review = db.execute_query(
            "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )

        if review:
            # 리뷰가 있으면 review_likes 확인
            row = db.execute_query(
                "SELECT 1 FROM review_likes WHERE user_id = ? AND review_id = ?",
                (user_id, review['id']),
                fetch_one=True
            )
            return row is not None
        else:
            # 리뷰가 없으면 activity_likes 확인
            row = db.execute_query(
                "SELECT 1 FROM activity_likes WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?",
                (user_id, activity_type, activity_user_id, item_id),
                fetch_one=True
            )
            return row is not None

    # 캐릭터 평가/리뷰
    elif activity_type == 'character_rating':
        review = db.execute_query(
            "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )

        if review:
            # 리뷰가 있으면 character_review_likes 확인
            row = db.execute_query(
                "SELECT 1 FROM character_review_likes WHERE user_id = ? AND review_id = ?",
                (user_id, review['id']),
                fetch_one=True
            )
            return row is not None
        else:
            # 리뷰가 없으면 activity_likes 확인
            row = db.execute_query(
                "SELECT 1 FROM activity_likes WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?",
                (user_id, activity_type, activity_user_id, item_id),
                fetch_one=True
            )
            return row is not None

    # 기타 활동은 activity_likes 테이블 확인
    row = db.execute_query(
        """
        SELECT 1 FROM activity_likes
        WHERE user_id = ? AND activity_type = ? AND activity_user_id = ? AND item_id = ?
        """,
        (user_id, activity_type, activity_user_id, item_id),
        fetch_one=True
    )
    return row is not None


def get_activity_like_count(activity_type: str, activity_user_id: int, item_id: int) -> int:
    """
    활동의 총 좋아요 수
    리뷰가 있으면 review의 likes_count, 없으면 activity_likes에서 COUNT
    """
    # 애니메이션 평가/리뷰
    if activity_type in ['anime_rating', 'anime_review']:
        row = db.execute_query(
            "SELECT likes_count FROM user_reviews WHERE user_id = ? AND anime_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )

        if row:
            # 리뷰가 있으면 likes_count 반환
            return row['likes_count']
        else:
            # 리뷰가 없으면 activity_likes에서 COUNT
            count_row = db.execute_query(
                "SELECT COUNT(*) as count FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?",
                (activity_type, activity_user_id, item_id),
                fetch_one=True
            )
            return count_row[0] if count_row else 0

    # 캐릭터 평가/리뷰
    elif activity_type == 'character_rating':
        row = db.execute_query(
            "SELECT likes_count FROM character_reviews WHERE user_id = ? AND character_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )

        if row:
            # 리뷰가 있으면 likes_count 반환
            return row['likes_count']
        else:
            # 리뷰가 없으면 activity_likes에서 COUNT
            count_row = db.execute_query(
                "SELECT COUNT(*) as count FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?",
                (activity_type, activity_user_id, item_id),
                fetch_one=True
            )
            return count_row[0] if count_row else 0

    # 기타 활동은 activity_likes 테이블에서 COUNT
    row = db.execute_query(
        """
        SELECT COUNT(*) as count FROM activity_likes
        WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?
        """,
        (activity_type, activity_user_id, item_id),
        fetch_one=True
    )
    return row[0] if row else 0


def get_activity_likes(activity_type: str, activity_user_id: int, item_id: int) -> List[Dict]:
    """
    활동에 좋아요를 누른 사용자 목록
    """
    rows = db.execute_query(
        """
        SELECT al.user_id, u.username, u.display_name, u.avatar_url, al.created_at
        FROM activity_likes al
        JOIN users u ON al.user_id = u.id
        WHERE al.activity_type = ? AND al.activity_user_id = ? AND al.item_id = ?
        ORDER BY al.created_at DESC
        """,
        (activity_type, activity_user_id, item_id)
    )
    return [dict_from_row(row) for row in rows]
