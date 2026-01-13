"""
Character Review Pydantic models
Request/Response schemas for character reviews
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CharacterReviewCreate(BaseModel):
    """캐릭터 리뷰 생성 요청"""
    character_id: int
    title: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=10, max_length=5000)
    is_spoiler: bool = False
    rating: Optional[float] = Field(None, ge=0.5, le=5.0, description="별점 (선택사항, 0.5~5.0)")


class CharacterReviewUpdate(BaseModel):
    """캐릭터 리뷰 수정 요청"""
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    is_spoiler: Optional[bool] = None


class CharacterReviewResponse(BaseModel):
    """캐릭터 리뷰 응답"""
    id: int
    user_id: int
    character_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    is_spoiler: Optional[bool] = False
    likes_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 추가 정보
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    character_name: Optional[str] = None
    user_rating: Optional[float] = None
    is_my_review: Optional[bool] = False
    user_liked: Optional[bool] = False
    otaku_score: Optional[float] = 0
    comments_count: Optional[int] = 0


class CharacterReviewListResponse(BaseModel):
    """캐릭터 리뷰 목록 응답"""
    items: List[CharacterReviewResponse]
    total: int
    page: int
    page_size: int
