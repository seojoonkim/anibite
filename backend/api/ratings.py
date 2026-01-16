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
    get_all_user_ratings,
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


@router.get("/me/all")
def get_all_my_ratings(
    rating: Optional[float] = Query(None, description="특정 평점 필터 (예: 5.0, 4.5)"),
    status_param: Optional[str] = Query(None, alias="status", description="상태 필터 (RATED, WANT_TO_WATCH, PASS)"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 모든 평점을 한 번에 조회 (RATED, WANT_TO_WATCH, PASS)

    3개의 API 호출을 1개로 줄여 로딩 속도 비약적 향상

    Query Parameters:
        rating: 특정 평점만 필터링 (예: 5.0, 4.5) - 순차 로딩용
        status: 특정 상태만 필터링 (RATED, WANT_TO_WATCH, PASS)

    Returns:
        {
            "rated": [...],
            "watchlist": [...],
            "pass": [...],
            "total_rated": 0,
            "total_watchlist": 0,
            "total_pass": 0,
            "average_rating": 0.0
        }
    """
    try:
        return get_all_user_ratings(current_user.id, rating_filter=rating, status_filter=status_param)
    except Exception as e:
        import traceback
        print(f"ERROR in get_all_my_ratings: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ratings: {str(e)}"
        )


@router.get("/me", response_model=UserRatingListResponse)
def get_my_ratings(
    status: Optional[RatingStatus] = Query(None, description="상태 필터"),
    without_review: bool = Query(False, description="리뷰 없는 평점만 조회"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="최대 개수"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 평점 목록 조회

    - status: RATED, WANT_TO_WATCH, PASS
    - without_review: True일 경우 리뷰가 없는 평점만 조회
    - limit: 최대 개수
    """
    return get_user_ratings(current_user.id, status, limit, without_review)


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


@router.get("/user/{user_id}/all")
def get_all_user_ratings_by_id(
    user_id: int
):
    """
    다른 사용자의 모든 평점을 한 번에 조회 (RATED, WANT_TO_WATCH, PASS)

    3개의 API 호출을 1개로 줄여 로딩 속도 비약적 향상

    Returns:
        {
            "rated": [...],
            "watchlist": [...],
            "pass": [...],
            "total_rated": 0,
            "total_watchlist": 0,
            "total_pass": 0,
            "average_rating": 0.0
        }
    """
    return get_all_user_ratings(user_id)


@router.get("/user/{user_id}", response_model=UserRatingListResponse)
def get_user_ratings_by_id(
    user_id: int,
    status: Optional[RatingStatus] = Query(None, description="상태 필터"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="최대 개수")
):
    """
    다른 사용자의 평점 목록 조회 (공개)

    - status: RATED, WANT_TO_WATCH, PASS
    - limit: 최대 개수
    """
    return get_user_ratings(user_id, status, limit)
