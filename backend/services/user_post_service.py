"""
User Post Service
사용자 일반 포스트 (상태 업데이트)
"""
from typing import List, Dict, Optional
from database import db, dict_from_row


def create_post(user_id: int, content: str) -> Dict:
    """
    일반 포스트 작성
    """
    post_id = db.execute_insert(
        """
        INSERT INTO user_posts (user_id, content)
        VALUES (?, ?)
        """,
        (user_id, content)
    )

    # 생성된 포스트 조회
    row = db.execute_query(
        """
        SELECT
            up.id,
            up.user_id,
            up.content,
            up.created_at,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE up.id = ?
        """,
        (post_id,),
        fetch_one=True
    )

    return dict_from_row(row) if row else None


def get_post(post_id: int) -> Optional[Dict]:
    """
    특정 포스트 조회
    """
    row = db.execute_query(
        """
        SELECT
            up.id,
            up.user_id,
            up.content,
            up.created_at,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE up.id = ?
        """,
        (post_id,),
        fetch_one=True
    )

    return dict_from_row(row) if row else None


def update_post(post_id: int, user_id: int, content: str) -> bool:
    """
    포스트 수정 (본인만 가능)
    """
    result = db.execute_update(
        """
        UPDATE user_posts
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        """,
        (content, post_id, user_id)
    )
    return result > 0


def delete_post(post_id: int, user_id: int) -> bool:
    """
    포스트 삭제 (본인만 가능)
    """
    result = db.execute_update(
        """
        DELETE FROM user_posts
        WHERE id = ? AND user_id = ?
        """,
        (post_id, user_id)
    )
    return result > 0


def get_user_posts(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    특정 사용자의 포스트 목록
    """
    rows = db.execute_query(
        """
        SELECT
            up.id,
            up.user_id,
            up.content,
            up.created_at,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE up.user_id = ?
        ORDER BY up.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    return [dict_from_row(row) for row in rows]
