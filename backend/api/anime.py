"""
Anime API Router
애니메이션 조회, 검색
"""
from fastapi import APIRouter, Query, HTTPException, status, Depends
from typing import Optional, List
from models.anime import AnimeResponse, AnimeDetailResponse, AnimeListResponse
from services.anime_service import (
    get_anime_list,
    get_anime_by_id,
    search_anime,
    get_popular_anime,
    get_top_rated_anime,
    get_all_genres
)
from api.deps import get_current_user_optional

router = APIRouter()


@router.get("/", response_model=AnimeListResponse)
def list_anime(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어"),
    genre: Optional[str] = Query(None, description="장르 필터"),
    season: Optional[str] = Query(None, description="시즌 (WINTER, SPRING, SUMMER, FALL)"),
    year: Optional[int] = Query(None, ge=1960, le=2030, description="방영 연도"),
    format: Optional[str] = Query(None, description="포맷 (TV, MOVIE, OVA, etc.)"),
    status: Optional[str] = Query(None, description="상태 (FINISHED, RELEASING, etc.)"),
    sort_by: str = Query("popularity", description="정렬 (popularity, score, trending, title, recent)"),
    exclude_rated: bool = Query(False, description="이미 평가한 항목 제외"),
    current_user = Depends(get_current_user_optional)
):
    """
    애니메이션 목록 조회 및 검색

    필터링 및 정렬 지원:
    - search: 검색어 (제목 검색)
    - genre: 장르
    - season: 시즌
    - year: 연도
    - format: 포맷
    - status: 상태
    - sort_by: 정렬 기준
    - exclude_rated: 이미 평가한 항목 제외 (로그인 필요)
    """
    # 검색어가 있으면 search_anime 사용
    if search:
        return search_anime(query=search, page=page, page_size=page_size)

    user_id = current_user.id if current_user and exclude_rated else None

    return get_anime_list(
        page=page,
        page_size=page_size,
        genre=genre,
        season=season,
        year=year,
        format=format,
        status=status,
        sort_by=sort_by,
        exclude_user_id=user_id
    )


@router.get("/search", response_model=AnimeListResponse)
def search(
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    애니메이션 검색

    제목(romaji, english, native)에서 검색
    """
    return search_anime(query=q, page=page, page_size=page_size)


@router.get("/popular", response_model=List[AnimeResponse])
def popular(limit: int = Query(50, ge=1, le=100)):
    """
    인기 애니메이션

    인기도 순으로 정렬
    """
    return get_popular_anime(limit=limit)


@router.get("/top-rated", response_model=List[AnimeResponse])
def top_rated(limit: int = Query(50, ge=1, le=100)):
    """
    최고 평점 애니메이션

    평균 점수 순으로 정렬
    """
    return get_top_rated_anime(limit=limit)


@router.get("/genres", response_model=List[str])
def genres():
    """
    모든 장르 목록
    """
    return get_all_genres()


@router.get("/{anime_id}", response_model=AnimeDetailResponse)
def get_anime(anime_id: int):
    """
    애니메이션 상세 정보

    장르, 태그, 스튜디오 정보 포함
    """
    anime = get_anime_by_id(anime_id)
    if anime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    return anime
