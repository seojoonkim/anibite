"""
Characters API Router
캐릭터 조회 및 평가
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from pydantic import BaseModel, Field
from models.user import UserResponse
from services.character_service import (
    get_characters_from_rated_anime,
    get_character_rating,
    create_or_update_character_rating,
    delete_character_rating,
    get_user_character_stats,
    get_character_detail
)
from api.deps import get_current_user

router = APIRouter()


class CharacterRatingCreate(BaseModel):
    character_id: int
    rating: float = Field(None, ge=0.5, le=5.0)
    status: str = Field(None)


class CharacterRatingResponse(BaseModel):
    id: int
    user_id: int
    character_id: int
    rating: float
    created_at: str
    updated_at: str


@router.get("/rated")
def get_my_rated_characters(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    내가 평가한 캐릭터들 조회
    """
    from services.character_service import get_user_rated_characters
    characters = get_user_rated_characters(current_user.id, limit, offset)
    return {
        'items': characters,
        'limit': limit,
        'offset': offset,
        'total': len(characters)
    }


@router.get("/from-rated-anime")
def get_characters_from_my_rated_anime(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    내가 평가한 애니메이션의 캐릭터들 조회
    """
    characters = get_characters_from_rated_anime(current_user.id, limit, offset)
    return {
        'items': characters,
        'limit': limit,
        'offset': offset,
        'total': len(characters)
    }


@router.post("/rate")
def rate_character(
    request: CharacterRatingCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 평가
    """
    # Validate rating (0.5 increments) if rating is provided
    if request.rating is not None:
        if (request.rating * 2) != int(request.rating * 2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be in 0.5 increments"
            )

    # Validate status if provided
    if request.status is not None and request.status not in ['RATED', 'WANT_TO_KNOW', 'NOT_INTERESTED']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status value"
        )

    result = create_or_update_character_rating(
        current_user.id,
        request.character_id,
        request.rating,
        request.status
    )

    return result


@router.get("/rating/{character_id}")
def get_my_character_rating(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    특정 캐릭터에 대한 내 평가 조회
    """
    rating = get_character_rating(current_user.id, character_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    return rating


@router.delete("/rating/{character_id}")
def delete_my_character_rating(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 평가 삭제
    """
    success = delete_character_rating(current_user.id, character_id)
    return {'success': success}


@router.get("/stats")
def get_my_character_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 캐릭터 평가 통계
    """
    return get_user_character_stats(current_user.id)


@router.get("/{character_id}")
def get_character_by_id(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 상세 정보 조회
    """
    character = get_character_detail(character_id, current_user.id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return character
