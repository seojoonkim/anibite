"""
Rating Pydantic models
Request/Response schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RatingStatus(str, Enum):
    """평점 상태"""
    RATED = "RATED"
    WANT_TO_WATCH = "WANT_TO_WATCH"
    PASS = "PASS"


class RatingCreate(BaseModel):
    """평점 생성 요청"""
    anime_id: int
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    status: RatingStatus = RatingStatus.RATED

    @field_validator('rating')
    @classmethod
    def validate_rating_increment(cls, v):
        if v is not None:
            # 0.5 단위로만 가능
            if (v * 2) % 1 != 0:
                raise ValueError('Rating must be in 0.5 increments')
        return v


class RatingUpdate(BaseModel):
    """평점 수정 요청"""
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    status: Optional[RatingStatus] = None

    @field_validator('rating')
    @classmethod
    def validate_rating_increment(cls, v):
        if v is not None:
            if (v * 2) % 1 != 0:
                raise ValueError('Rating must be in 0.5 increments')
        return v


class RatingResponse(BaseModel):
    """평점 응답"""
    id: int
    user_id: int
    anime_id: int
    rating: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    # 추가 정보 (조인 시)
    anime_title: Optional[str] = None
    anime_cover_image: Optional[str] = None
    title_romaji: Optional[str] = None
    title_english: Optional[str] = None
    title_korean: Optional[str] = None
    image_url: Optional[str] = None
    season_year: Optional[int] = None
    episodes: Optional[int] = None


class UserRatingListResponse(BaseModel):
    """사용자 평점 목록"""
    items: List[RatingResponse]
    total: int
    average_rating: Optional[float]
