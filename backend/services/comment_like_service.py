"""
Comment Like Service
댓글 좋아요 관리
"""
from typing import Dict, List
from database import db, dict_from_row


def like_comment(user_id: int, comment_id: int) -> bool:
    """
    댓글에 좋아요 추가
    """
    try:
        db.execute_insert(
            """
            INSERT INTO comment_likes (user_id, comment_id)
            VALUES (?, ?)
            """,
            (user_id, comment_id)
        )
        return True
    except Exception as e:
        # 이미 좋아요한 경우 무시
        return False


def unlike_comment(user_id: int, comment_id: int) -> bool:
    """
    댓글 좋아요 취소
    """
    try:
        result = db.execute_update(
            """
            DELETE FROM comment_likes
            WHERE user_id = ? AND comment_id = ?
            """,
            (user_id, comment_id)
        )
        return result > 0
    except Exception:
        return False


def is_comment_liked(user_id: int, comment_id: int) -> bool:
    """
    사용자가 해당 댓글에 좋아요를 눌렀는지 확인
    """
    row = db.execute_query(
        """
        SELECT 1 FROM comment_likes
        WHERE user_id = ? AND comment_id = ?
        """,
        (user_id, comment_id),
        fetch_one=True
    )
    return row is not None


def get_comment_like_count(comment_id: int) -> int:
    """
    댓글의 총 좋아요 수
    """
    row = db.execute_query(
        """
        SELECT COUNT(*) as count FROM comment_likes
        WHERE comment_id = ?
        """,
        (comment_id,),
        fetch_one=True
    )
    return row[0] if row else 0


def get_comment_likes(comment_id: int) -> List[Dict]:
    """
    댓글에 좋아요를 누른 사용자 목록
    """
    rows = db.execute_query(
        """
        SELECT cl.user_id, u.username, u.display_name, u.avatar_url, cl.created_at
        FROM comment_likes cl
        JOIN users u ON cl.user_id = u.id
        WHERE cl.comment_id = ?
        ORDER BY cl.created_at DESC
        """,
        (comment_id,)
    )
    return [dict_from_row(row) for row in rows]
