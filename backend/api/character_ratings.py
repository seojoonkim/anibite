"""
Character Rating API Router
캐릭터 평점 생성, 수정, 삭제, 조회 (애니메이션 평점 API와 동일한 구조)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from pydantic import BaseModel, Field
from models.user import UserResponse
from services.character_service import (
    create_or_update_character_rating,
    get_character_rating,
    get_user_character_ratings,
    get_all_user_character_ratings,
    delete_character_rating
)
from api.deps import get_current_user

router = APIRouter()


class CharacterRatingCreate(BaseModel):
    character_id: int
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    status: str = Field('RATED')  # RATED, WANT_TO_KNOW, NOT_INTERESTED


class CharacterRatingResponse(BaseModel):
    id: int
    user_id: int
    character_id: int
    rating: Optional[float]
    status: str
    created_at: str
    updated_at: str


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_rating(
    rating_data: CharacterRatingCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 평점 생성 또는 수정

    - **character_id**: 캐릭터 ID
    - **rating**: 평점 (0.5~5.0, 0.5 단위)
    - **status**: RATED(평가함), WANT_TO_KNOW(알고싶어요), NOT_INTERESTED(관심없어요)

    이미 평점이 있으면 수정됨
    """
    # Validate rating (0.5 increments) if rating is provided
    if rating_data.rating is not None:
        if (rating_data.rating * 2) != int(rating_data.rating * 2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be in 0.5 increments"
            )

    # WANT_TO_KNOW 또는 NOT_INTERESTED일 때는 rating을 NULL로 설정
    final_rating = rating_data.rating if rating_data.status == 'RATED' else None

    return create_or_update_character_rating(
        current_user.id,
        rating_data.character_id,
        final_rating,
        rating_data.status
    )


@router.get("/me/all")
def get_all_my_ratings(
    rating: Optional[float] = Query(None, description="특정 평점 필터 (예: 5.0, 4.5)"),
    status: Optional[str] = Query(None, description="상태 필터 (RATED, WANT_TO_KNOW, NOT_INTERESTED)"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 모든 캐릭터 평점을 한 번에 조회 (RATED, WANT_TO_KNOW, NOT_INTERESTED)

    3개의 API 호출을 1개로 줄여 로딩 속도 비약적 향상

    Query Parameters:
        rating: 특정 평점만 필터링 (예: 5.0, 4.5) - 순차 로딩용
        status: 특정 상태만 필터링 (RATED, WANT_TO_KNOW, NOT_INTERESTED)

    Returns:
        {
            "rated": [...],
            "want_to_know": [...],
            "not_interested": [...],
            "total_rated": 0,
            "total_want_to_know": 0,
            "total_not_interested": 0,
            "average_rating": 0.0
        }
    """
    return get_all_user_character_ratings(current_user.id, rating_filter=rating, status_filter=status)


@router.get("/me")
def get_my_ratings(
    status: Optional[str] = Query(None, description="상태 필터 (RATED, WANT_TO_KNOW, NOT_INTERESTED)"),
    without_review: bool = Query(False, description="리뷰 없는 평점만 조회"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="최대 개수"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 캐릭터 평점 목록 조회

    - status: RATED, WANT_TO_KNOW, NOT_INTERESTED
    - without_review: True일 경우 리뷰가 없는 평점만 조회
    - limit: 최대 개수
    """
    return get_user_character_ratings(current_user.id, status, limit, without_review)


@router.get("/character/{character_id}")
def get_my_rating_for_character(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    특정 캐릭터에 대한 내 평점 조회

    평점이 없으면 null 반환
    """
    rating = get_character_rating(current_user.id, character_id)
    return rating


@router.delete("/character/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_rating(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 평점 삭제

    성공하면 204 No Content
    """
    success = delete_character_rating(current_user.id, character_id)
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
    다른 사용자의 모든 캐릭터 평점을 한 번에 조회 (RATED, WANT_TO_KNOW, NOT_INTERESTED)

    3개의 API 호출을 1개로 줄여 로딩 속도 비약적 향상

    Returns:
        {
            "rated": [...],
            "want_to_know": [...],
            "not_interested": [...],
            "total_rated": 0,
            "total_want_to_know": 0,
            "total_not_interested": 0,
            "average_rating": 0.0
        }
    """
    return get_all_user_character_ratings(user_id)


@router.get("/user/{user_id}")
def get_user_ratings_by_id(
    user_id: int,
    status: Optional[str] = Query(None, description="상태 필터"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="최대 개수")
):
    """
    다른 사용자의 캐릭터 평점 목록 조회 (공개)

    - status: RATED, WANT_TO_KNOW, NOT_INTERESTED
    - limit: 최대 개수
    """
    return get_user_character_ratings(user_id, status, limit)
