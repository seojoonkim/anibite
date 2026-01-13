"""
Rating API Router
평점 생성, 수정, 삭제, 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from models.rating import (
    RatingCreate,
    RatingUpdate,
    RatingResponse,
    UserRatingListResponse,
    RatingStatus
)
from models.user import UserResponse
from services.rating_service import (
    create_or_update_rating,
    get_user_rating_for_anime,
    get_user_ratings,
    delete_rating
)
from api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def create_rating(
    rating_data: RatingCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    평점 생성 또는 수정

    - **anime_id**: 애니메이션 ID
    - **rating**: 평점 (0.5~5.0, 0.5 단위)
    - **status**: RATED(평가함), WANT_TO_WATCH(보고싶어요), PASS(패스)

    이미 평점이 있으면 수정됨
    """
    return create_or_update_rating(current_user.id, rating_data)


@router.get("/me", response_model=UserRatingListResponse)
def get_my_ratings(
    status: Optional[RatingStatus] = Query(None, description="상태 필터"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="최대 개수"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 평점 목록 조회

    - status: RATED, WANT_TO_WATCH, PASS
    - limit: 최대 개수
    """
    return get_user_ratings(current_user.id, status, limit)


@router.get("/anime/{anime_id}", response_model=Optional[RatingResponse])
def get_my_rating_for_anime(
    anime_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    특정 애니메이션에 대한 내 평점 조회

    평점이 없으면 null 반환
    """
    rating = get_user_rating_for_anime(current_user.id, anime_id)
    return rating


@router.delete("/anime/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_rating(
    anime_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    평점 삭제

    성공하면 204 No Content
    """
    success = delete_rating(current_user.id, anime_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
