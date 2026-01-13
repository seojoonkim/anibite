"""
Anime Pydantic models
Request/Response schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AnimeResponse(BaseModel):
    """애니메이션 기본 정보"""
    id: int
    title_romaji: str
    title_english: Optional[str]
    title_native: Optional[str]
    title_korean: Optional[str]
    title_korean_official: Optional[int] = 0  # 1: 오피셜 제목, 0: 번역 제목
    type: Optional[str]
    format: Optional[str]
    status: Optional[str]
    description: Optional[str]
    season: Optional[str]
    season_year: Optional[int]
    episodes: Optional[int]
    duration: Optional[int]
    cover_image_url: Optional[str]
    cover_image_color: Optional[str]
    banner_image_url: Optional[str]
    average_score: Optional[int]
    popularity: Optional[int]
    favourites: Optional[int]
    source: Optional[str]
    is_adult: bool
    season_number: Optional[int] = None  # 시즌 번호 (PREQUEL 수 + 1)
    site_rating_count: Optional[int] = 0  # 우리 사이트 평가 수
    site_average_rating: Optional[float] = None  # 우리 사이트 평균 평점
    user_rating_status: Optional[str] = None  # 현재 사용자의 평가 상태 (RATED, WANT_TO_WATCH, PASS)
    genres: List[str] = []  # 장르 목록
    airing_status: Optional[str] = None  # 방영 상태 (status 별칭)


class AnimeDetailResponse(AnimeResponse):
    """애니메이션 상세 정보 (장르, 태그, 캐릭터, 스태프 등 포함)"""
    genres: List[str] = []
    tags: List[dict] = []
    studios: List[dict] = []
    characters: List[dict] = []  # 캐릭터 & 성우
    staff: List[dict] = []  # 제작진 (감독, 각본 등)
    recommendations: List[dict] = []  # 추천 애니메이션
    external_links: List[dict] = []  # 외부 링크 (스트리밍 등)
    trailer_url: Optional[str]
    site_url: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    site_rating_distribution: List[dict] = []  # 평점 분포


class AnimeListResponse(BaseModel):
    """애니메이션 목록 응답 (페이지네이션)"""
    items: List[AnimeResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
