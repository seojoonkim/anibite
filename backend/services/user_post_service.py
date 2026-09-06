"""
User Post Service
사용자 일반 포스트 (상태 업데이트)
"""
from typing import List, Dict, Optional
from database import db, dict_from_row


@db.atomic
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

    sync_post_projection(post_id, user_id)

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


@db.atomic
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
    if result:
        sync_post_projection(post_id, user_id)
    return result > 0


@db.atomic
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
    if result:
        sync_post_projection(post_id, user_id)
    return result > 0


@db.atomic
def sync_post_projection(post_id: int, user_id: int):
    """Retain hidden tombstones and their social references after deletion."""
    post = get_post(post_id)
    if not post:
        db.execute_update(
            "UPDATE activities SET review_content=NULL,review_title=NULL,rating=NULL WHERE activity_type='user_post' AND user_id=? AND item_id=?",
            (user_id, post_id),
        )
        return
    db.execute_update("""
        INSERT INTO activities(activity_type,user_id,item_id,username,display_name,avatar_url,otaku_score,review_content,activity_time)
        VALUES ('user_post',?,?,?,?,?,?,?,?)
        ON CONFLICT(activity_type,user_id,item_id) DO UPDATE SET
            review_content=excluded.review_content,username=excluded.username,
            display_name=excluded.display_name,avatar_url=excluded.avatar_url,
            otaku_score=excluded.otaku_score,updated_at=CURRENT_TIMESTAMP
        """, (user_id, post_id, post['username'], post['display_name'], post['avatar_url'],
              post['otaku_score'], post['content'], post['created_at']))


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
