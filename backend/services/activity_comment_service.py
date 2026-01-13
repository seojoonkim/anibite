"""
Activity Comment Service
피드 활동에 대한 댓글 처리
"""
from typing import List, Dict, Optional
from database import db, dict_from_row


def get_activity_comments(activity_type: str, activity_user_id: int, item_id: int) -> List[Dict]:
    """
    특정 활동에 대한 댓글 목록 조회 (계층 구조 포함)
    최상위 댓글과 그 답글들을 조회
    애니메이션/캐릭터 평가와 리뷰는 review_comments 테이블 사용
    """
    print(f"[get_activity_comments] Called with: activity_type={activity_type}, activity_user_id={activity_user_id}, item_id={item_id}")
    # 애니메이션 리뷰와 평가는 review_comments 사용 (리뷰가 있는 경우)
    # 리뷰가 없으면 activity_comments로 폴백
    if activity_type in ['anime_review', 'review', 'anime_rating']:
        # 리뷰 ID 찾기
        review = db.execute_query(
            "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )

        if review:
            review_id = review['id']

            # 최상위 댓글 조회
            rows = db.execute_query(
                """
                SELECT
                    rc.id,
                    rc.user_id,
                    rc.content,
                    rc.created_at,
                    rc.parent_comment_id,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score
                FROM review_comments rc
                JOIN users u ON rc.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                WHERE rc.review_id = ?
                    AND rc.review_type = 'anime'
                    AND rc.parent_comment_id IS NULL
                ORDER BY rc.created_at ASC
                """,
                (review_id,)
            )

            comments = [dict_from_row(row) for row in rows]

            # 각 최상위 댓글에 대한 답글 조회
            for comment in comments:
                reply_rows = db.execute_query(
                    """
                    SELECT
                        rc.id,
                        rc.user_id,
                        rc.content,
                        rc.created_at,
                        rc.parent_comment_id,
                        u.username,
                        u.display_name,
                        u.avatar_url,
                        COALESCE(us.otaku_score, 0) as otaku_score
                    FROM review_comments rc
                    JOIN users u ON rc.user_id = u.id
                    LEFT JOIN user_stats us ON u.id = us.user_id
                    WHERE rc.parent_comment_id = ?
                    ORDER BY rc.created_at ASC
                    """,
                    (comment['id'],)
                )
                comment['replies'] = [dict_from_row(row) for row in reply_rows]

            return comments

    # 캐릭터 리뷰와 평가는 review_comments 사용 (리뷰가 있는 경우)
    # 리뷰가 없으면 activity_comments로 폴백
    elif activity_type in ['character_review', 'character_rating']:
        print(f"[get_activity_comments] Character review/rating detected. Checking for review...")
        # 캐릭터 리뷰 ID 찾기
        review = db.execute_query(
            "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )
        print(f"[get_activity_comments] Review found: {review}")

        if review:
            review_id = review['id']

            # 최상위 댓글 조회
            rows = db.execute_query(
                """
                SELECT
                    rc.id,
                    rc.user_id,
                    rc.content,
                    rc.created_at,
                    rc.parent_comment_id,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score
                FROM review_comments rc
                JOIN users u ON rc.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                WHERE rc.review_id = ?
                    AND rc.review_type = 'character'
                    AND rc.parent_comment_id IS NULL
                ORDER BY rc.created_at ASC
                """,
                (review_id,)
            )

            comments = [dict_from_row(row) for row in rows]

            # 각 최상위 댓글에 대한 답글 조회
            for comment in comments:
                reply_rows = db.execute_query(
                    """
                    SELECT
                        rc.id,
                        rc.user_id,
                        rc.content,
                        rc.created_at,
                        rc.parent_comment_id,
                        u.username,
                        u.display_name,
                        u.avatar_url,
                        COALESCE(us.otaku_score, 0) as otaku_score
                    FROM review_comments rc
                    JOIN users u ON rc.user_id = u.id
                    LEFT JOIN user_stats us ON u.id = us.user_id
                    WHERE rc.parent_comment_id = ?
                    ORDER BY rc.created_at ASC
                    """,
                    (comment['id'],)
                )
                comment['replies'] = [dict_from_row(row) for row in reply_rows]

            return comments
        else:
            print(f"[get_activity_comments] No review found for character_rating, will use activity_comments")

    # 기타 활동은 activity_comments 사용
    print(f"[get_activity_comments] Using activity_comments table for activity_type={activity_type}")
    rows = db.execute_query(
        """
        SELECT
            ac.id,
            ac.user_id,
            ac.content,
            ac.created_at,
            ac.parent_comment_id,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM activity_comments ac
        JOIN users u ON ac.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE ac.activity_type = ?
            AND ac.activity_user_id = ?
            AND ac.item_id = ?
            AND ac.parent_comment_id IS NULL
        ORDER BY ac.created_at ASC
        """,
        (activity_type, activity_user_id, item_id)
    )

    comments = [dict_from_row(row) for row in rows]

    # 각 최상위 댓글에 대한 답글 조회
    for comment in comments:
        reply_rows = db.execute_query(
            """
            SELECT
                ac.id,
                ac.user_id,
                ac.content,
                ac.created_at,
                ac.parent_comment_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score
            FROM activity_comments ac
            JOIN users u ON ac.user_id = u.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE ac.parent_comment_id = ?
            ORDER BY ac.created_at ASC
            """,
            (comment['id'],)
        )
        comment['replies'] = [dict_from_row(row) for row in reply_rows]

    return comments


def create_activity_comment(
    user_id: int,
    activity_type: str,
    activity_user_id: int,
    item_id: int,
    content: str,
    parent_comment_id: Optional[int] = None
) -> Dict:
    """
    활동에 댓글 작성 (답글 포함)
    리뷰(anime_review, character_review)와 평가(anime_rating, character_rating)인 경우 review_comments 테이블 사용
    """
    print(f"[create_activity_comment] Called with: activity_type={activity_type}, activity_user_id={activity_user_id}, item_id={item_id}, user_id={user_id}")
    # 애니메이션 리뷰 또는 평가에 대한 댓글은 review_comments 테이블 사용
    # 리뷰가 없으면 activity_comments로 폴백
    if activity_type in ['anime_review', 'review', 'anime_rating']:
        # 리뷰 ID 찾기
        review = db.execute_query(
            "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )
        if not review:
            # 리뷰가 없으면 activity_comments로 폴백
            pass
        else:
            review_id = review['id']
            review_type = 'anime'

            # parent_comment_id 확인
            if parent_comment_id:
                parent_row = db.execute_query(
                    "SELECT depth FROM review_comments WHERE id = ?",
                    (parent_comment_id,),
                    fetch_one=True
                )
                if not parent_row:
                    raise ValueError("Parent comment not found")
                if parent_row['depth'] == 2:
                    raise ValueError("Cannot reply to a reply (max depth is 2)")
                depth = 2
            else:
                depth = 1

            # review_comments에 저장
            comment_id = db.execute_insert(
                """
                INSERT INTO review_comments (
                    user_id, review_id, review_type, parent_comment_id, content, depth,
                    likes_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (user_id, review_id, review_type, parent_comment_id, content, depth)
            )

            # 생성된 댓글 조회
            row = db.execute_query(
                """
                SELECT
                    rc.id,
                    rc.user_id,
                    rc.content,
                    rc.created_at,
                    rc.parent_comment_id,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score
                FROM review_comments rc
                JOIN users u ON rc.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                WHERE rc.id = ?
                """,
                (comment_id,),
                fetch_one=True
            )

            return dict_from_row(row) if row else None

    # 캐릭터 리뷰 또는 평가에 대한 댓글은 review_comments 테이블 사용
    # 리뷰가 없으면 activity_comments로 폴백
    elif activity_type in ['character_review', 'character_rating']:
        print(f"[create_activity_comment] Character review/rating detected. Checking for review...")
        # 캐릭터 리뷰 ID 찾기
        review = db.execute_query(
            "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
            (activity_user_id, item_id),
            fetch_one=True
        )
        print(f"[create_activity_comment] Review found: {review}")
        if not review:
            # 리뷰가 없으면 activity_comments로 폴백
            print(f"[create_activity_comment] No review found, will use activity_comments table")
            pass
        else:
            review_id = review['id']
            review_type = 'character'

            # parent_comment_id 확인
            if parent_comment_id:
                parent_row = db.execute_query(
                    "SELECT depth FROM review_comments WHERE id = ?",
                    (parent_comment_id,),
                    fetch_one=True
                )
                if not parent_row:
                    raise ValueError("Parent comment not found")
                if parent_row['depth'] == 2:
                    raise ValueError("Cannot reply to a reply (max depth is 2)")
                depth = 2
            else:
                depth = 1

            # review_comments에 저장
            comment_id = db.execute_insert(
                """
                INSERT INTO review_comments (
                    user_id, review_id, review_type, parent_comment_id, content, depth,
                    likes_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (user_id, review_id, review_type, parent_comment_id, content, depth)
            )

            # 생성된 댓글 조회
            row = db.execute_query(
                """
                SELECT
                    rc.id,
                    rc.user_id,
                    rc.content,
                    rc.created_at,
                    rc.parent_comment_id,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score
                FROM review_comments rc
                JOIN users u ON rc.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                WHERE rc.id = ?
                """,
                (comment_id,),
                fetch_one=True
            )

            return dict_from_row(row) if row else None

    # 기타 활동(anime_rating, character_rating 등)은 activity_comments 사용
    print(f"[create_activity_comment] Using activity_comments table for activity_type={activity_type}")
    # parent_comment_id가 있는 경우, 해당 댓글이 최상위 댓글인지 확인
    if parent_comment_id:
        parent_row = db.execute_query(
            "SELECT parent_comment_id FROM activity_comments WHERE id = ?",
            (parent_comment_id,),
            fetch_one=True
        )
        if parent_row and parent_row[0] is not None:
            # 이미 답글인 경우, 대댓글은 허용하지 않음
            raise ValueError("Cannot reply to a reply")

    print(f"[create_activity_comment] Inserting into activity_comments: user_id={user_id}, activity_type={activity_type}, activity_user_id={activity_user_id}, item_id={item_id}")
    comment_id = db.execute_insert(
        """
        INSERT INTO activity_comments (user_id, activity_type, activity_user_id, item_id, content, parent_comment_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, activity_type, activity_user_id, item_id, content, parent_comment_id)
    )
    print(f"[create_activity_comment] Comment created with id={comment_id}")

    # 생성된 댓글 조회
    row = db.execute_query(
        """
        SELECT
            ac.id,
            ac.user_id,
            ac.content,
            ac.created_at,
            ac.parent_comment_id,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM activity_comments ac
        JOIN users u ON ac.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE ac.id = ?
        """,
        (comment_id,),
        fetch_one=True
    )

    return dict_from_row(row) if row else None


def delete_activity_comment(comment_id: int, user_id: int) -> bool:
    """
    댓글 삭제 (본인만 가능)
    review_comments와 activity_comments 모두 확인 및 삭제
    답글(replies)도 함께 삭제
    """
    # 먼저 review_comments에서 확인
    review_comment = db.execute_query(
        "SELECT id, review_id, review_type FROM review_comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id),
        fetch_one=True
    )

    if review_comment:
        # review_comments에서 삭제 (CASCADE로 대댓글도 자동 삭제)
        db.execute_update(
            "DELETE FROM review_comments WHERE id = ? AND user_id = ?",
            (comment_id, user_id)
        )
        return True

    # activity_comments에서 확인 및 삭제
    activity_comment = db.execute_query(
        "SELECT id FROM activity_comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id),
        fetch_one=True
    )

    if activity_comment:
        # activity_comments에서 삭제 (CASCADE로 대댓글도 자동 삭제)
        db.execute_update(
            "DELETE FROM activity_comments WHERE id = ? AND user_id = ?",
            (comment_id, user_id)
        )
        return True

    return False


def get_comment_counts_for_activities(activities: List[Dict]) -> Dict:
    """
    여러 활동에 대한 댓글 수 일괄 조회
    리뷰는 review_comments, 기타는 activity_comments
    """
    if not activities:
        return {}

    counts = {}

    for activity in activities:
        activity_key = f"{activity['activity_type']}_{activity['user_id']}_{activity['item_id']}"
        activity_type = activity['activity_type']

        # 리뷰인 경우 review_comments에서 조회
        if activity_type in ['anime_review', 'review']:
            review = db.execute_query(
                "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
                (activity['user_id'], activity['item_id']),
                fetch_one=True
            )
            if review:
                row = db.execute_query(
                    "SELECT COUNT(*) as count FROM review_comments WHERE review_id = ? AND review_type = 'anime'",
                    (review['id'],),
                    fetch_one=True
                )
                counts[activity_key] = row[0] if row else 0
            else:
                counts[activity_key] = 0

        elif activity_type == 'character_review':
            review = db.execute_query(
                "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                (activity['user_id'], activity['item_id']),
                fetch_one=True
            )
            if review:
                row = db.execute_query(
                    "SELECT COUNT(*) as count FROM review_comments WHERE review_id = ? AND review_type = 'character'",
                    (review['id'],),
                    fetch_one=True
                )
                counts[activity_key] = row[0] if row else 0
            else:
                counts[activity_key] = 0

        else:
            # 기타 활동은 activity_comments에서 조회
            row = db.execute_query(
                """
                SELECT COUNT(*) as count
                FROM activity_comments
                WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?
                """,
                (activity['activity_type'], activity['user_id'], activity['item_id']),
                fetch_one=True
            )
            counts[activity_key] = row[0] if row else 0

    return counts
