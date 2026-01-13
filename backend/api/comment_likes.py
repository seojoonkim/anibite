"""
Comment Likes API Router
댓글 좋아요
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.comment_like_service import (
    like_comment,
    unlike_comment,
    is_comment_liked,
    get_comment_like_count,
    get_comment_likes
)
from models.user import UserResponse
from api.deps import get_current_user

router = APIRouter()


class CommentLikeRequest(BaseModel):
    comment_id: int


@router.post("/")
def toggle_comment_like(
    request: CommentLikeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 좋아요 토글 (좋아요 추가/취소)
    """
    # 이미 좋아요한 경우 취소
    if is_comment_liked(current_user.id, request.comment_id):
        unlike_comment(current_user.id, request.comment_id)
        liked = False
    else:
        like_comment(current_user.id, request.comment_id)
        liked = True

    return {
        "liked": liked,
        "like_count": get_comment_like_count(request.comment_id)
    }


@router.get("/check/{comment_id}")
def check_comment_like(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 좋아요 상태 확인
    """
    return {
        "liked": is_comment_liked(current_user.id, comment_id),
        "like_count": get_comment_like_count(comment_id)
    }


@router.get("/list/{comment_id}")
def get_comment_like_list(comment_id: int) -> List[Dict]:
    """
    댓글에 좋아요를 누른 사용자 목록
    """
    return get_comment_likes(comment_id)
