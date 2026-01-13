"""
Comment Pydantic models
Request/Response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommentCreate(BaseModel):
    """댓글 생성 요청"""
    review_id: int
    review_type: str = "anime"  # Phase 1에서는 anime만
    content: str = Field(..., min_length=1, max_length=1000)


class ReplyCreate(BaseModel):
    """대댓글 생성 요청"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """댓글 응답"""
    model_config = {'extra': 'ignore'}

    id: int
    user_id: int
    review_id: int
    review_type: str
    parent_comment_id: Optional[int]
    content: str
    likes_count: int
    depth: int
    created_at: datetime
    updated_at: datetime

    # 추가 정보
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    display_name: Optional[str] = None
    otaku_score: Optional[float] = None


class CommentListResponse(BaseModel):
    """댓글 목록 응답"""
    items: List[CommentResponse]
    total: int
