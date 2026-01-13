"""
Comment API Router
댓글 생성, 삭제, 조회, 좋아요
"""
from fastapi import APIRouter, Depends, HTTPException, status
from models.comment import CommentCreate, ReplyCreate, CommentResponse, CommentListResponse
from models.user import UserResponse
from services.comment_service import (
    create_comment,
    create_reply,
    delete_comment,
    get_review_comments,
    like_comment,
    unlike_comment
)
from api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create(
    comment_data: CommentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 작성 (1 depth)

    - **review_id**: 리뷰 ID
    - **review_type**: "anime" (Phase 1)
    - **content**: 댓글 내용 (1~1000자)
    """
    return create_comment(current_user.id, comment_data)


@router.post("/{comment_id}/reply", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def reply(
    comment_id: int,
    reply_data: ReplyCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    대댓글 작성 (2 depth)

    댓글에만 답글 가능, 대댓글에는 불가 (최대 2 depth)
    """
    return create_reply(comment_id, current_user.id, reply_data)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 삭제

    본인의 댓글만 삭제 가능
    대댓글이 있어도 함께 삭제됨 (CASCADE)
    """
    delete_comment(comment_id, current_user.id)


@router.get("/review/{review_id}", response_model=CommentListResponse)
def get_comments(
    review_id: int,
    review_type: str = "anime"
):
    """
    리뷰의 댓글 목록

    계층 구조로 정렬 (댓글 → 대댓글)
    """
    return get_review_comments(review_id, review_type)


@router.post("/{comment_id}/like", response_model=CommentResponse)
def like(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 좋아요

    이미 좋아요한 경우 400 에러
    """
    return like_comment(comment_id, current_user.id)


@router.delete("/{comment_id}/like", response_model=CommentResponse)
def unlike(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    댓글 좋아요 취소
    """
    return unlike_comment(comment_id, current_user.id)
