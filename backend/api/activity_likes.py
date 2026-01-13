"""
Activity Likes API Router
활동 좋아요
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.activity_like_service import (
    like_activity,
    unlike_activity,
    is_activity_liked,
    get_activity_like_count,
    get_activity_likes
)
from models.user import UserResponse
from api.deps import get_current_user

router = APIRouter()


class ActivityLikeRequest(BaseModel):
    activity_type: str
    activity_user_id: int
    item_id: int


@router.post("/")
def toggle_activity_like(
    request: ActivityLikeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    활동 좋아요 토글 (좋아요 추가/취소)
    """
    # 이미 좋아요한 경우 취소
    if is_activity_liked(current_user.id, request.activity_type, request.activity_user_id, request.item_id):
        unlike_activity(current_user.id, request.activity_type, request.activity_user_id, request.item_id)
        liked = False
    else:
        like_activity(current_user.id, request.activity_type, request.activity_user_id, request.item_id)
        liked = True

    return {
        "liked": liked,
        "like_count": get_activity_like_count(request.activity_type, request.activity_user_id, request.item_id)
    }


@router.get("/check")
def check_activity_like(
    activity_type: str,
    activity_user_id: int,
    item_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    활동 좋아요 상태 확인
    """
    return {
        "liked": is_activity_liked(current_user.id, activity_type, activity_user_id, item_id),
        "like_count": get_activity_like_count(activity_type, activity_user_id, item_id)
    }


@router.get("/list")
def get_activity_like_list(
    activity_type: str,
    activity_user_id: int,
    item_id: int
) -> List[Dict]:
    """
    활동에 좋아요를 누른 사용자 목록
    """
    return get_activity_likes(activity_type, activity_user_id, item_id)
