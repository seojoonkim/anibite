"""
User Posts API Router
사용자 일반 포스트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict
from services.user_post_service import (
    create_post,
    get_post,
    update_post,
    delete_post,
    get_user_posts
)
from models.user import UserResponse
from api.deps import get_current_user

router = APIRouter()


class PostCreate(BaseModel):
    content: str


class PostUpdate(BaseModel):
    content: str


@router.post("/")
def create_user_post(
    request: PostCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    일반 포스트 작성
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post content is required"
        )

    post = create_post(current_user.id, request.content)
    return post


@router.get("/{post_id}")
def get_user_post(post_id: int):
    """
    특정 포스트 조회
    """
    post = get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.put("/{post_id}")
def update_user_post(
    post_id: int,
    request: PostUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    포스트 수정 (본인만 가능)
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post content is required"
        )

    success = update_post(post_id, current_user.id, request.content)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or unauthorized"
        )
    return {"success": True}


@router.delete("/{post_id}")
def delete_user_post(
    post_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    포스트 삭제 (본인만 가능)
    """
    success = delete_post(post_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or unauthorized"
        )
    return {"success": True}


@router.get("/user/{user_id}")
def get_posts_by_user(
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    특정 사용자의 포스트 목록
    """
    return get_user_posts(user_id, limit, offset)
