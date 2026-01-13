"""
Follow Service
팔로우 관련 비즈니스 로직
"""
from typing import List, Dict, Optional
from database import db, dict_from_row


def follow_user(follower_id: int, following_id: int) -> bool:
    """
    사용자 팔로우
    """
    if follower_id == following_id:
        return False

    try:
        db.execute_insert(
            """
            INSERT INTO user_follows (follower_id, following_id)
            VALUES (?, ?)
            """,
            (follower_id, following_id)
        )
        return True
    except Exception as e:
        # Already following or other error
        print(f"Follow error: {e}")
        return False


def unfollow_user(follower_id: int, following_id: int) -> bool:
    """
    사용자 언팔로우
    """
    db.execute_update(
        """
        DELETE FROM user_follows
        WHERE follower_id = ? AND following_id = ?
        """,
        (follower_id, following_id)
    )
    return True


def is_following(follower_id: int, following_id: int) -> bool:
    """
    팔로우 여부 확인
    """
    row = db.execute_query(
        """
        SELECT id FROM user_follows
        WHERE follower_id = ? AND following_id = ?
        """,
        (follower_id, following_id),
        fetch_one=True
    )
    return row is not None


def get_followers(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    특정 사용자를 팔로우하는 사용자 목록
    """
    rows = db.execute_query(
        """
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.avatar_url,
            u.created_at,
            uf.created_at as followed_at
        FROM user_follows uf
        JOIN users u ON uf.follower_id = u.id
        WHERE uf.following_id = ?
        ORDER BY uf.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )
    return [dict_from_row(row) for row in rows]


def get_following(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    특정 사용자가 팔로우하는 사용자 목록
    """
    rows = db.execute_query(
        """
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.avatar_url,
            u.created_at,
            uf.created_at as followed_at
        FROM user_follows uf
        JOIN users u ON uf.following_id = u.id
        WHERE uf.follower_id = ?
        ORDER BY uf.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )
    return [dict_from_row(row) for row in rows]


def get_follow_counts(user_id: int) -> Dict:
    """
    팔로워/팔로잉 수 조회
    """
    row = db.execute_query(
        """
        SELECT
            (SELECT COUNT(*) FROM user_follows WHERE following_id = ?) as followers_count,
            (SELECT COUNT(*) FROM user_follows WHERE follower_id = ?) as following_count
        """,
        (user_id, user_id),
        fetch_one=True
    )
    return dict_from_row(row) if row else {
        'followers_count': 0,
        'following_count': 0
    }
