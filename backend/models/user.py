"""
User Pydantic models
Request/Response schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# ==================== Request Models ====================

class UserRegister(BaseModel):
    """회원가입 요청"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    display_name: Optional[str] = Field(None, max_length=50)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


class UserLogin(BaseModel):
    """로그인 요청"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    display_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class PasswordUpdate(BaseModel):
    """비밀번호 변경"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Response Models ====================

class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    username: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """공개 사용자 정보 (이메일 제외)"""
    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserStatsResponse(BaseModel):
    """사용자 통계"""
    user_id: int
    total_rated: int
    total_want_to_watch: int
    total_pass: int
    average_rating: Optional[float]
    total_reviews: int
    total_character_ratings: int
    total_watch_time_minutes: int
    otaku_score: float
    favorite_genre: Optional[str]
    updated_at: datetime


class UserProfileResponse(BaseModel):
    """사용자 프로필 (정보 + 통계)"""
    user: UserPublicResponse
    stats: Optional[UserStatsResponse]
