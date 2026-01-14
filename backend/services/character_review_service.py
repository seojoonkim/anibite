"""
Character Review Service
캐릭터 리뷰 생성, 수정, 삭제, 조회
"""
from typing import List, Optional
from fastapi import HTTPException, status
from database import db, dict_from_row
from models.character_review import (
    CharacterReviewCreate,
    CharacterReviewUpdate,
    CharacterReviewResponse,
    CharacterReviewListResponse
)


def create_character_review(user_id: int, review_data: CharacterReviewCreate) -> CharacterReviewResponse:
    """캐릭터 리뷰 생성"""

    # 캐릭터 존재 확인
    character_exists = db.execute_query(
        "SELECT id FROM character WHERE id = ?",
        (review_data.character_id,),
        fetch_one=True
    )

    if not character_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 중복 확인
    existing = db.execute_query(
        "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
        (user_id, review_data.character_id),
        fetch_one=True
    )

    if existing:
        # 이미 리뷰가 있으면 업데이트
        return update_character_review(
            existing['id'],
            user_id,
            CharacterReviewUpdate(
                content=review_data.content,
                title=review_data.title,
                is_spoiler=review_data.is_spoiler
            )
        )

    # 별점이 함께 제공된 경우 먼저 저장
    if review_data.rating is not None:
        try:
            from services.character_service import rate_character
            # 별점 저장 (이미 _sync_character_rating_to_activities 호출됨)
            rate_character(user_id, review_data.character_id, review_data.rating)
        except Exception as e:
            # 별점 저장 실패해도 리뷰는 계속 진행
            print(f"Warning: Failed to save character rating: {e}")

    # 리뷰 생성
    review_id = db.execute_insert(
        """
        INSERT INTO character_reviews (
            user_id, character_id, title, content, is_spoiler,
            likes_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_id, review_data.character_id, review_data.title,
         review_data.content, 1 if review_data.is_spoiler else 0)
    )

    # Sync to activities (리뷰 생성 시 activities 업데이트)
    from services.character_service import _sync_character_rating_to_activities
    _sync_character_rating_to_activities(user_id, review_data.character_id)

    return get_character_review_by_id(review_id)


def update_character_review(review_id: int, user_id: int, review_data: CharacterReviewUpdate) -> CharacterReviewResponse:
    """캐릭터 리뷰 수정 (별점도 함께 업데이트 가능)"""

    # 리뷰 존재 및 권한 확인
    existing = db.execute_query(
        "SELECT user_id, character_id FROM character_reviews WHERE id = ?",
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

    character_id = existing['character_id']

    # 별점이 제공되면 먼저 업데이트
    if review_data.rating is not None:
        from services.character_service import create_or_update_character_rating
        create_or_update_character_rating(user_id, character_id, rating=review_data.rating)

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

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(review_id)

        db.execute_update(
            f"UPDATE character_reviews SET {', '.join(update_fields)} WHERE id = ?",
            tuple(params)
        )

    # Sync to activities (리뷰 수정 시 activities도 업데이트)
    # Note: 별점 업데이트 시 이미 sync가 호출되었지만, 리뷰 내용도 반영하기 위해 다시 호출
    from services.character_service import _sync_character_rating_to_activities
    _sync_character_rating_to_activities(user_id, character_id)

    return get_character_review_by_id(review_id)


def delete_character_review(review_id: int, user_id: int) -> bool:
    """캐릭터 리뷰 삭제 (관련 댓글과 좋아요도 함께 삭제)"""

    # 권한 확인
    existing = db.execute_query(
        "SELECT user_id FROM character_reviews WHERE id = ?",
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
        "DELETE FROM review_comments WHERE review_id = ? AND review_type = 'character'",
        (review_id,)
    )

    # 관련 좋아요 삭제 (character_review_likes)
    db.execute_update(
        "DELETE FROM character_review_likes WHERE review_id = ?",
        (review_id,)
    )

    # 리뷰 삭제
    db.execute_update("DELETE FROM character_reviews WHERE id = ?", (review_id,))

    return True


def get_character_review_by_id(review_id: int) -> Optional[CharacterReviewResponse]:
    """캐릭터 리뷰 ID로 조회"""

    row = db.execute_query(
        """
        SELECT
            r.*,
            u.username,
            u.avatar_url,
            c.name_full as character_name,
            cr.rating as user_rating,
            (SELECT COUNT(*) FROM review_comments
             WHERE review_id = r.id AND review_type = 'character') as comments_count
        FROM character_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN character c ON r.character_id = c.id
        LEFT JOIN character_ratings cr ON r.user_id = cr.user_id AND r.character_id = cr.character_id
        WHERE r.id = ?
        """,
        (review_id,),
        fetch_one=True
    )

    if row is None:
        return None

    return CharacterReviewResponse(**dict_from_row(row))


def get_character_reviews(
    character_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user_id: Optional[int] = None
) -> CharacterReviewListResponse:
    """캐릭터의 리뷰와 평점 목록 (평점만 있는 것도 포함)"""

    offset = (page - 1) * page_size

    # 전체 개수 (평점이 있는 모든 사용자)
    total = db.execute_query(
        "SELECT COUNT(*) as total FROM character_ratings WHERE character_id = ?",
        (character_id,),
        fetch_one=True
    )['total']

    # 리뷰와 평점 목록 (평점 기준, 리뷰가 있으면 함께 표시)
    rows = db.execute_query(
        """
        SELECT
            COALESCE(r.id, cr.id * -1) as id,
            cr.id as rating_id,
            cr.user_id,
            cr.character_id,
            cr.rating as user_rating,
            cr.created_at as rating_created_at,
            r.id as review_id,
            r.content,
            r.title,
            r.is_spoiler,
            COALESCE(r.likes_count, 0) as likes_count,
            COALESCE(r.created_at, cr.created_at) as created_at,
            r.updated_at,
            u.username,
            u.display_name,
            u.avatar_url,
            us.otaku_score,
            c.name_full as character_name,
            (SELECT COUNT(*) FROM review_comments WHERE review_id = r.id AND review_type = 'character') as comments_count,
            CASE WHEN ? IS NOT NULL AND r.id IS NOT NULL THEN
                (SELECT COUNT(*) FROM character_review_likes crl WHERE crl.review_id = r.id AND crl.user_id = ?)
            ELSE 0 END as user_liked
        FROM character_ratings cr
        JOIN users u ON cr.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN character_reviews r ON cr.user_id = r.user_id AND cr.character_id = r.character_id
        WHERE cr.character_id = ?
        ORDER BY
            CASE WHEN r.id IS NOT NULL THEN 0 ELSE 1 END,
            COALESCE(r.likes_count, 0) DESC,
            COALESCE(r.created_at, cr.created_at) DESC
        LIMIT ? OFFSET ?
        """,
        (current_user_id, current_user_id, character_id, page_size, offset)
    )

    items = []
    for row in rows:
        review_dict = dict_from_row(row)
        # is_my_review 플래그 설정
        if current_user_id:
            review_dict['is_my_review'] = review_dict['user_id'] == current_user_id
        else:
            review_dict['is_my_review'] = False
        # Convert user_liked to boolean
        review_dict['user_liked'] = bool(review_dict.get('user_liked', 0))
        items.append(CharacterReviewResponse(**review_dict))

    return CharacterReviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


def get_my_character_review(user_id: int, character_id: int) -> Optional[CharacterReviewResponse]:
    """내가 작성한 특정 캐릭터의 리뷰 조회 (평점만 있는 것도 포함)"""

    # 먼저 평점이 있는지 확인 (평점 기준으로 조회)
    row = db.execute_query(
        """
        SELECT
            COALESCE(r.id, cr.id * -1) as id,
            cr.id as rating_id,
            cr.user_id,
            cr.character_id,
            cr.rating as user_rating,
            cr.created_at as rating_created_at,
            r.id as review_id,
            r.content,
            r.title,
            r.is_spoiler,
            COALESCE(r.likes_count, 0) as likes_count,
            COALESCE(r.created_at, cr.created_at) as created_at,
            r.updated_at,
            u.username,
            u.display_name,
            u.avatar_url,
            us.otaku_score,
            c.name_full as character_name,
            (SELECT COUNT(*) FROM review_comments WHERE review_id = r.id AND review_type = 'character') as comments_count,
            CASE WHEN r.id IS NOT NULL THEN
                (SELECT COUNT(*) FROM character_review_likes crl WHERE crl.review_id = r.id AND crl.user_id = ?)
            ELSE 0 END as user_liked
        FROM character_ratings cr
        JOIN users u ON cr.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN character_reviews r ON cr.user_id = r.user_id AND cr.character_id = r.character_id
        WHERE cr.user_id = ? AND cr.character_id = ?
        """,
        (user_id, user_id, character_id),
        fetch_one=True
    )

    if row is None:
        return None

    review_dict = dict_from_row(row)
    review_dict['is_my_review'] = True
    review_dict['user_liked'] = bool(review_dict.get('user_liked', 0))
    return CharacterReviewResponse(**review_dict)


def like_character_review(review_id: int, user_id: int) -> CharacterReviewResponse:
    """캐릭터 리뷰 좋아요"""

    # 리뷰 존재 확인
    review_exists = db.execute_query(
        "SELECT id FROM character_reviews WHERE id = ?",
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
        "SELECT user_id FROM character_review_likes WHERE user_id = ? AND review_id = ?",
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
        "INSERT INTO character_review_likes (user_id, review_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, review_id)
    )

    # likes_count 증가
    db.execute_update(
        "UPDATE character_reviews SET likes_count = likes_count + 1 WHERE id = ?",
        (review_id,)
    )

    return get_character_review_by_id(review_id)


def unlike_character_review(review_id: int, user_id: int) -> CharacterReviewResponse:
    """캐릭터 리뷰 좋아요 취소"""

    rowcount = db.execute_update(
        "DELETE FROM character_review_likes WHERE user_id = ? AND review_id = ?",
        (user_id, review_id)
    )

    if rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )

    # likes_count 감소
    db.execute_update(
        "UPDATE character_reviews SET likes_count = likes_count - 1 WHERE id = ? AND likes_count > 0",
        (review_id,)
    )

    return get_character_review_by_id(review_id)
