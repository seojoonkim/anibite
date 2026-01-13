"""
Follows API Router
팔로우 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from models.user import UserResponse
from services.follow_service import (
    follow_user,
    unfollow_user,
    is_following,
    get_followers,
    get_following,
    get_follow_counts
)
from api.deps import get_current_user

router = APIRouter()


@router.post("/{user_id}/follow")
def follow(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    사용자 팔로우
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )

    success = follow_user(current_user.id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already following or invalid user"
        )

    return {"success": True, "is_following": True}


@router.delete("/{user_id}/follow")
def unfollow(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    사용자 언팔로우
    """
    success = unfollow_user(current_user.id, user_id)
    return {"success": success, "is_following": False}


@router.get("/{user_id}/is-following")
def check_following(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    팔로우 여부 확인
    """
    following = is_following(current_user.id, user_id)
    return {"is_following": following}


@router.get("/{user_id}/followers")
def get_user_followers(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    사용자의 팔로워 목록
    """
    followers = get_followers(user_id, limit, offset)
    return {
        'items': followers,
        'total': len(followers),
        'limit': limit,
        'offset': offset
    }


@router.get("/{user_id}/following")
def get_user_following(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    사용자가 팔로우하는 목록
    """
    following = get_following(user_id, limit, offset)
    return {
        'items': following,
        'total': len(following),
        'limit': limit,
        'offset': offset
    }


@router.get("/{user_id}/follow-counts")
def get_user_follow_counts(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    팔로워/팔로잉 수 조회
    """
    return get_follow_counts(user_id)
