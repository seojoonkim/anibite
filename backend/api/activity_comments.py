"""
Activity Comments API Router
피드 활동 댓글 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from models.user import UserResponse
from services.activity_comment_service import (
    get_activity_comments,
    create_activity_comment,
    delete_activity_comment
)
from api.deps import get_current_user

router = APIRouter()


class ActivityCommentCreate(BaseModel):
    activity_type: str
    activity_user_id: int
    item_id: int
    content: str
    parent_comment_id: Optional[int] = None


@router.get("/")
def get_comments(
    activity_type: str = Query(...),
    activity_user_id: int = Query(...),
    item_id: int = Query(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    특정 활동에 대한 댓글 목록 조회
    """
    comments = get_activity_comments(activity_type, activity_user_id, item_id)
    return {"items": comments, "total": len(comments)}


@router.post("/")
def create_comment(
    request: ActivityCommentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    활동에 댓글 작성 (답글 포함)
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment content is required"
        )

    try:
        comment = create_activity_comment(
            current_user.id,
            request.activity_type,
            request.activity_user_id,
            request.item_id,
            request.content,
            request.parent_comment_id
        )
        return comment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 삭제 (본인만 가능)
    """
    success = delete_activity_comment(comment_id, current_user.id)
    return {"success": success}
