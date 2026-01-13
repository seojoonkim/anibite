"""
Review Service
리뷰 생성, 수정, 삭제, 조회
"""
from typing import List, Optional
from fastapi import HTTPException, status
from database import db, dict_from_row
from models.review import ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse


def create_review(user_id: int, review_data: ReviewCreate) -> ReviewResponse:
    """리뷰 생성"""

    # 애니메이션 존재 확인
    anime_exists = db.execute_query(
        "SELECT id FROM anime WHERE id = ?",
        (review_data.anime_id,),
        fetch_one=True
    )

    if not anime_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )

    # 중복 확인
    existing = db.execute_query(
        "SELECT id FROM user_reviews WHERE user_id = ? AND anime_id = ?",
        (user_id, review_data.anime_id),
        fetch_one=True
    )

    if existing:
        # 이미 리뷰가 있으면 업데이트
        return update_review(
            existing['id'],
            user_id,
            ReviewUpdate(
                content=review_data.content,
                title=review_data.title,
                is_spoiler=review_data.is_spoiler
            )
        )

    # 평점 ID 가져오기 (있으면)
    rating_row = db.execute_query(
        "SELECT id FROM user_ratings WHERE user_id = ? AND anime_id = ?",
        (user_id, review_data.anime_id),
        fetch_one=True
    )
    rating_id = rating_row['id'] if rating_row else None

    # 리뷰 생성
    review_id = db.execute_insert(
        """
        INSERT INTO user_reviews (
            user_id, anime_id, rating_id, title, content, is_spoiler,
            likes_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_id, review_data.anime_id, rating_id, review_data.title,
         review_data.content, 1 if review_data.is_spoiler else 0)
    )

    # 사용자 통계 업데이트 (리뷰 수)
    from services.rating_service import _update_user_stats
    _update_user_stats(user_id)

    return get_review_by_id(review_id)


def update_review(review_id: int, user_id: int, review_data: ReviewUpdate) -> ReviewResponse:
    """리뷰 수정"""

    # 리뷰 존재 및 권한 확인
    existing = db.execute_query(
        "SELECT user_id FROM user_reviews WHERE id = ?",
        (review_id,),
        fetch_one=True
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if existing['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )

    # 수정할 필드만 업데이트
    update_fields = []
    params = []

    if review_data.title is not None:
        update_fields.append("title = ?")
        params.append(review_data.title)

    if review_data.content is not None:
        update_fields.append("content = ?")
        params.append(review_data.content)

    if review_data.is_spoiler is not None:
        update_fields.append("is_spoiler = ?")
        params.append(1 if review_data.is_spoiler else 0)

    if not update_fields:
        # 수정할 내용이 없으면 기존 리뷰 반환
        return get_review_by_id(review_id)

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(review_id)

    db.execute_update(
        f"UPDATE user_reviews SET {', '.join(update_fields)} WHERE id = ?",
        tuple(params)
    )

    return get_review_by_id(review_id)


def delete_review(review_id: int, user_id: int) -> bool:
    """리뷰 삭제 (관련 댓글과 좋아요도 함께 삭제)"""

    # 권한 확인
    existing = db.execute_query(
        "SELECT user_id FROM user_reviews WHERE id = ?",
        (review_id,),
        fetch_one=True
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if existing['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )

    # 관련 댓글 삭제 (review_comments)
    db.execute_update(
        "DELETE FROM review_comments WHERE review_id = ? AND review_type = 'anime'",
        (review_id,)
    )

    # 관련 좋아요 삭제 (review_likes)
    db.execute_update(
        "DELETE FROM review_likes WHERE review_id = ?",
        (review_id,)
    )

    # 리뷰 삭제
    db.execute_update("DELETE FROM user_reviews WHERE id = ?", (review_id,))

    # 사용자 통계 업데이트
    from services.rating_service import _update_user_stats
    _update_user_stats(user_id)

    return True


def get_review_by_id(review_id: int) -> Optional[ReviewResponse]:
    """리뷰 ID로 조회"""

    row = db.execute_query(
        """
        SELECT
            r.*,
            u.username,
            u.avatar_url,
            a.title_romaji as anime_title,
            ur.rating as user_rating
        FROM user_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN anime a ON r.anime_id = a.id
        LEFT JOIN user_ratings ur ON r.rating_id = ur.id
        WHERE r.id = ?
        """,
        (review_id,),
        fetch_one=True
    )

    if row is None:
        return None

    return ReviewResponse(**dict_from_row(row))


def get_anime_reviews(
    anime_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user_id: Optional[int] = None
) -> ReviewListResponse:
    """애니메이션의 리뷰와 평점 목록 (평점만 있는 것도 포함)"""

    offset = (page - 1) * page_size

    # 전체 개수 (평점이 있는 모든 사용자)
    total = db.execute_query(
        "SELECT COUNT(*) as total FROM user_ratings WHERE anime_id = ?",
        (anime_id,),
        fetch_one=True
    )['total']

    # 리뷰와 평점 목록 (평점 기준, 리뷰가 있으면 함께 표시)
    rows = db.execute_query(
        """
        SELECT
            COALESCE(r.id, ur.id * -1) as id,
            ur.id as rating_id,
            ur.user_id,
            ur.anime_id,
            ur.rating as user_rating,
            ur.created_at as rating_created_at,
            r.id as review_id,
            r.title,
            r.content,
            r.is_spoiler,
            (SELECT COUNT(*) FROM activity_likes
             WHERE activity_type = 'anime_rating'
             AND activity_user_id = ur.user_id
             AND item_id = ur.anime_id) as likes_count,
            COALESCE(r.created_at, ur.created_at) as created_at,
            r.updated_at,
            u.username,
            u.display_name,
            u.avatar_url,
            us.otaku_score,
            a.title_romaji as anime_title,
            COALESCE(
                (SELECT COUNT(*) FROM review_comments c WHERE c.review_id = r.id AND c.review_type = 'anime'),
                0
            ) as comments_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes
                 WHERE user_id = ?
                 AND activity_type = 'anime_rating'
                 AND activity_user_id = ur.user_id
                 AND item_id = ur.anime_id) > 0
            ELSE 0 END as user_liked
        FROM user_ratings ur
        JOIN users u ON ur.user_id = u.id
        JOIN anime a ON ur.anime_id = a.id
        LEFT JOIN user_reviews r ON ur.user_id = r.user_id AND ur.anime_id = r.anime_id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE ur.anime_id = ?
        ORDER BY
            CASE WHEN r.id IS NOT NULL THEN 0 ELSE 1 END,
            (SELECT COUNT(*) FROM activity_likes
             WHERE activity_type = 'anime_rating'
             AND activity_user_id = ur.user_id
             AND item_id = ur.anime_id) DESC,
            COALESCE(r.created_at, ur.created_at) DESC
        LIMIT ? OFFSET ?
        """,
        (current_user_id, current_user_id, anime_id, page_size, offset)
    )

    items = []
    for row in rows:
        review_dict = dict_from_row(row)
        # Add is_my_review field
        if current_user_id:
            review_dict['is_my_review'] = review_dict['user_id'] == current_user_id
        else:
            review_dict['is_my_review'] = False
        # Convert user_liked to boolean
        review_dict['user_liked'] = bool(review_dict.get('user_liked', 0))
        items.append(ReviewResponse(**review_dict))

    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


def get_user_reviews(user_id: int, page: int = 1, page_size: int = 20) -> ReviewListResponse:
    """사용자의 리뷰 목록"""

    offset = (page - 1) * page_size

    # 전체 개수
    total = db.execute_query(
        "SELECT COUNT(*) as total FROM user_reviews WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )['total']

    # 리뷰 목록
    rows = db.execute_query(
        """
        SELECT
            r.*,
            u.username,
            u.avatar_url,
            a.title_romaji as anime_title,
            ur.rating as user_rating
        FROM user_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN anime a ON r.anime_id = a.id
        LEFT JOIN user_ratings ur ON r.rating_id = ur.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, page_size, offset)
    )

    items = [ReviewResponse(**dict_from_row(row)) for row in rows]

    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


def get_my_review(user_id: int, anime_id: int) -> Optional[ReviewResponse]:
    """내가 작성한 특정 애니메이션의 리뷰 조회"""

    row = db.execute_query(
        """
        SELECT
            r.*,
            u.username,
            u.avatar_url,
            a.title_romaji as anime_title,
            ur.rating as user_rating
        FROM user_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN anime a ON r.anime_id = a.id
        LEFT JOIN user_ratings ur ON r.rating_id = ur.id
        WHERE r.user_id = ? AND r.anime_id = ?
        """,
        (user_id, anime_id),
        fetch_one=True
    )

    if row is None:
        return None

    return ReviewResponse(**dict_from_row(row))


def like_review(review_id: int, user_id: int) -> ReviewResponse:
    """리뷰 좋아요"""

    # 리뷰 존재 확인
    review_exists = db.execute_query(
        "SELECT id FROM user_reviews WHERE id = ?",
        (review_id,),
        fetch_one=True
    )

    if not review_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # 중복 확인
    existing_like = db.execute_query(
        "SELECT user_id FROM review_likes WHERE user_id = ? AND review_id = ?",
        (user_id, review_id),
        fetch_one=True
    )

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already liked this review"
        )

    # 좋아요 추가
    db.execute_insert(
        "INSERT INTO review_likes (user_id, review_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, review_id)
    )

    # likes_count 업데이트
    db.execute_update(
        "UPDATE user_reviews SET likes_count = likes_count + 1 WHERE id = ?",
        (review_id,)
    )

    return get_review_by_id(review_id)


def unlike_review(review_id: int, user_id: int) -> ReviewResponse:
    """리뷰 좋아요 취소"""

    rowcount = db.execute_update(
        "DELETE FROM review_likes WHERE user_id = ? AND review_id = ?",
        (user_id, review_id)
    )

    if rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )

    # likes_count 업데이트
    db.execute_update(
        "UPDATE user_reviews SET likes_count = CASE WHEN likes_count > 0 THEN likes_count - 1 ELSE 0 END WHERE id = ?",
        (review_id,)
    )

    return get_review_by_id(review_id)
