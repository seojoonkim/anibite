"""
Character Review API Router
캐릭터 리뷰 생성, 수정, 삭제, 조회, 좋아요
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.character_review import (
    CharacterReviewCreate,
    CharacterReviewUpdate,
    CharacterReviewResponse,
    CharacterReviewListResponse
)
from models.user import UserResponse
from services.character_review_service import (
    create_character_review,
    update_character_review,
    delete_character_review,
    get_character_review_by_id,
    get_character_reviews,
    get_my_character_review,
    like_character_review,
    unlike_character_review
)
from api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=CharacterReviewResponse, status_code=status.HTTP_201_CREATED)
def create(
    review_data: CharacterReviewCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 리뷰 작성

    - **character_id**: 캐릭터 ID
    - **title**: 제목 (선택)
    - **content**: 내용 (10~5000자)
    - **is_spoiler**: 스포일러 여부
    """
    return create_character_review(current_user.id, review_data)


@router.put("/{review_id}", response_model=CharacterReviewResponse)
def update(
    review_id: int,
    review_data: CharacterReviewUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 리뷰 수정

    본인의 리뷰만 수정 가능
    """
    return update_character_review(review_id, current_user.id, review_data)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 리뷰 삭제

    본인의 리뷰만 삭제 가능
    """
    delete_character_review(review_id, current_user.id)


@router.delete("/character/{character_id}/my-review", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_character_review(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 캐릭터 리뷰 삭제 (character_id로 삭제)

    본인의 리뷰만 삭제 가능
    """
    from services.character_review_service import delete_character_review_by_character
    delete_character_review_by_character(current_user.id, character_id)


@router.get("/{review_id}", response_model=CharacterReviewResponse)
def get_review(review_id: int):
    """
    캐릭터 리뷰 상세 조회
    """
    review = get_character_review_by_id(review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review


@router.get("/character/{character_id}/my-review", response_model=Optional[CharacterReviewResponse])
def get_my_character_review_endpoint(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내가 작성한 특정 캐릭터의 리뷰 조회
    리뷰가 없으면 null 반환
    """
    return get_my_character_review(current_user.id, character_id)


@router.get("/character/{character_id}", response_model=CharacterReviewListResponse)
def get_character_review_list(
    character_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터의 리뷰 목록

    좋아요 순으로 정렬
    """
    return get_character_reviews(character_id, page, page_size, current_user.id)


@router.post("/{review_id}/like", response_model=CharacterReviewResponse)
def like(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 리뷰 좋아요

    이미 좋아요한 경우 400 에러
    """
    return like_character_review(review_id, current_user.id)


@router.delete("/{review_id}/like", response_model=CharacterReviewResponse)
def unlike(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 리뷰 좋아요 취소
    """
    return unlike_character_review(review_id, current_user.id)
