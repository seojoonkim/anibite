"""
Review API Router
리뷰 생성, 수정, 삭제, 조회, 좋아요
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.review import ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse
from models.user import UserResponse
from services.review_service import (
    create_review,
    update_review,
    delete_review,
    get_review_by_id,
    get_anime_reviews,
    get_user_reviews,
    get_my_review,
    like_review,
    unlike_review
)
from api.deps import get_current_user, get_current_user_optional

router = APIRouter()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create(
    review_data: ReviewCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    리뷰 작성

    - **anime_id**: 애니메이션 ID
    - **title**: 제목 (선택)
    - **content**: 내용 (10~5000자)
    - **is_spoiler**: 스포일러 여부
    """
    return create_review(current_user.id, review_data)


@router.put("/{review_id}", response_model=ReviewResponse)
def update(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    리뷰 수정

    본인의 리뷰만 수정 가능
    """
    return update_review(review_id, current_user.id, review_data)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    리뷰 삭제

    본인의 리뷰만 삭제 가능
    """
    delete_review(review_id, current_user.id)


@router.delete("/anime/{anime_id}/my-review", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_anime_review(
    anime_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 애니메이션 리뷰 삭제 (anime_id로 삭제)

    본인의 리뷰만 삭제 가능
    """
    from services.review_service import delete_review_by_anime
    delete_review_by_anime(current_user.id, anime_id)


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int):
    """
    리뷰 상세 조회
    """
    review = get_review_by_id(review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return review


@router.get("/anime/{anime_id}/my-review", response_model=Optional[ReviewResponse])
def get_my_anime_review(
    anime_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내가 작성한 특정 애니메이션의 리뷰 조회
    리뷰가 없으면 null 반환
    """
    return get_my_review(current_user.id, anime_id)


@router.get("/anime/{anime_id}", response_model=ReviewListResponse)
def get_anime_review_list(
    anime_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user_optional)
):
    """
    애니메이션의 리뷰 목록

    좋아요 순으로 정렬
    """
    return get_anime_reviews(anime_id, page, page_size, current_user.id if current_user else None)


@router.get("/user/{user_id}", response_model=ReviewListResponse)
def get_user_review_list(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    사용자의 리뷰 목록

    최신순으로 정렬
    """
    return get_user_reviews(user_id, page, page_size)


@router.post("/{review_id}/like", response_model=ReviewResponse)
def like(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    리뷰 좋아요

    이미 좋아요한 경우 400 에러
    """
    return like_review(review_id, current_user.id)


@router.delete("/{review_id}/like", response_model=ReviewResponse)
def unlike(
    review_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    리뷰 좋아요 취소
    """
    return unlike_review(review_id, current_user.id)
