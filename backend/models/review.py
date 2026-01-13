"""
Review Pydantic models
Request/Response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewCreate(BaseModel):
    """리뷰 생성 요청"""
    anime_id: int
    title: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=10, max_length=5000)
    is_spoiler: bool = False


class ReviewUpdate(BaseModel):
    """리뷰 수정 요청"""
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    is_spoiler: Optional[bool] = None


class ReviewResponse(BaseModel):
    """리뷰 응답"""
    id: int
    user_id: int
    anime_id: int
    title: Optional[str]
    content: Optional[str] = None
    is_spoiler: Optional[bool] = False
    likes_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 추가 정보
    username: Optional[str] = None
    display_name: Optional[str] = None
    user_avatar: Optional[str] = None
    anime_title: Optional[str] = None
    user_rating: Optional[float] = None
    is_my_review: Optional[bool] = False
    comments_count: Optional[int] = 0
    user_liked: Optional[bool] = False
    otaku_score: Optional[float] = 0


class ReviewListResponse(BaseModel):
    """리뷰 목록 응답"""
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
