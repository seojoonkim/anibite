"""
Comment Service
댓글 생성, 삭제, 조회, 좋아요
"""
from typing import List, Optional
from fastapi import HTTPException, status
from database import db, dict_from_row
from models.comment import CommentCreate, ReplyCreate, CommentResponse, CommentListResponse


def create_comment(user_id: int, comment_data: CommentCreate) -> CommentResponse:
    """댓글 생성 (1 depth)"""

    # 리뷰 존재 확인
    if comment_data.review_type == "anime":
        review_exists = db.execute_query(
            "SELECT id FROM user_reviews WHERE id = ?",
            (comment_data.review_id,),
            fetch_one=True
        )
    elif comment_data.review_type == "character":
        review_exists = db.execute_query(
            "SELECT id FROM character_reviews WHERE id = ?",
            (comment_data.review_id,),
            fetch_one=True
        )
    else:
        # 지원하지 않는 리뷰 타입
        review_exists = None

    if not review_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # 댓글 생성
    comment_id = db.execute_insert(
        """
        INSERT INTO review_comments (
            user_id, review_id, review_type, content, depth,
            likes_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_id, comment_data.review_id, comment_data.review_type, comment_data.content)
    )

    return get_comment_by_id(comment_id)


def create_reply(parent_comment_id: int, user_id: int, reply_data: ReplyCreate) -> CommentResponse:
    """대댓글 생성 (2 depth)"""

    # 부모 댓글 확인
    parent = db.execute_query(
        "SELECT id, review_id, review_type, depth FROM review_comments WHERE id = ?",
        (parent_comment_id,),
        fetch_one=True
    )

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found"
        )

    if parent['depth'] == 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reply to a reply (max depth is 2)"
        )

    # 대댓글 생성
    comment_id = db.execute_insert(
        """
        INSERT INTO review_comments (
            user_id, review_id, review_type, parent_comment_id, content, depth,
            likes_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 2, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_id, parent['review_id'], parent['review_type'], parent_comment_id, reply_data.content)
    )

    return get_comment_by_id(comment_id)


def delete_comment(comment_id: int, user_id: int) -> bool:
    """댓글 삭제 (review_comments 및 activity_comments 모두 삭제)"""

    # 권한 확인
    existing = db.execute_query(
        "SELECT user_id FROM review_comments WHERE id = ?",
        (comment_id,),
        fetch_one=True
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if existing['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )

    # review_comments에서 삭제 (CASCADE로 대댓글도 자동 삭제)
    db.execute_update("DELETE FROM review_comments WHERE id = ?", (comment_id,))

    # activity_comments에서도 삭제 (알림 제거)
    db.execute_update("DELETE FROM activity_comments WHERE id = ?", (comment_id,))

    return True


def get_comment_by_id(comment_id: int) -> Optional[CommentResponse]:
    """댓글 ID로 조회"""

    row = db.execute_query(
        """
        SELECT c.*, u.username, u.avatar_url, u.display_name, COALESCE(us.otaku_score, 0) as otaku_score
        FROM review_comments c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE c.id = ?
        """,
        (comment_id,),
        fetch_one=True
    )

    if row is None:
        return None

    return CommentResponse(**dict_from_row(row))


def get_review_comments(review_id: int, review_type: str = "anime") -> CommentListResponse:
    """리뷰의 댓글 목록 (계층 구조)"""

    # 전체 개수
    total = db.execute_query(
        "SELECT COUNT(*) as total FROM review_comments WHERE review_id = ? AND review_type = ?",
        (review_id, review_type),
        fetch_one=True
    )['total']

    # 모든 댓글 조회 (depth 순, 생성 시간 순)
    rows = db.execute_query(
        """
        SELECT c.*, u.username, u.avatar_url, u.display_name, COALESCE(us.otaku_score, 0) as otaku_score
        FROM review_comments c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE c.review_id = ? AND c.review_type = ?
        ORDER BY
            COALESCE(c.parent_comment_id, c.id),
            c.depth,
            c.created_at
        """,
        (review_id, review_type)
    )

    items = [CommentResponse(**dict_from_row(row)) for row in rows]

    return CommentListResponse(items=items, total=total)


def like_comment(comment_id: int, user_id: int) -> CommentResponse:
    """댓글 좋아요"""

    # 댓글 존재 확인
    comment_exists = db.execute_query(
        "SELECT id FROM review_comments WHERE id = ?",
        (comment_id,),
        fetch_one=True
    )

    if not comment_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # 중복 확인
    existing_like = db.execute_query(
        "SELECT user_id FROM comment_likes WHERE user_id = ? AND comment_id = ?",
        (user_id, comment_id),
        fetch_one=True
    )

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already liked this comment"
        )

    # 좋아요 추가 (trigger가 자동으로 likes_count 증가)
    db.execute_insert(
        "INSERT INTO comment_likes (user_id, comment_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, comment_id)
    )

    return get_comment_by_id(comment_id)


def unlike_comment(comment_id: int, user_id: int) -> CommentResponse:
    """댓글 좋아요 취소"""

    rowcount = db.execute_update(
        "DELETE FROM comment_likes WHERE user_id = ? AND comment_id = ?",
        (user_id, comment_id)
    )

    if rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )

    return get_comment_by_id(comment_id)
