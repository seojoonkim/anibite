"""
Rating Pages API Router
평가 페이지 전용 초고속 API (목표: 0.1초 이내)
"""
from fastapi import APIRouter, Query, Depends
from typing import List, Dict
from models.user import UserResponse
from services.rating_page_service import (
    get_anime_for_rating,
    get_characters_for_rating,
    get_anime_for_rating_stats,
    get_characters_for_rating_stats
)
from api.deps import get_current_user

router = APIRouter()


@router.get("/anime")
def get_anime_to_rate(
    limit: int = Query(50, ge=1, le=100, description="한 번에 가져올 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    애니메이션 평가 페이지 - 초고속 쿼리

    특징:
    - 미평가 + WANT_TO_WATCH 항목 반환
    - 랜덤성 내장 (매번 조금씩 다른 순서)
    - 서브쿼리 0개
    - 목표: 0.1초 이내

    Returns:
        {
            "items": [...],
            "limit": 50,
            "offset": 0,
            "has_more": true
        }
    """
    items = get_anime_for_rating(current_user.id, limit, offset)

    return {
        'items': items,
        'limit': limit,
        'offset': offset,
        'has_more': len(items) == limit
    }


@router.get("/anime/stats")
def get_anime_rating_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    애니메이션 평가 통계

    Returns:
        {
            "total": 3000,
            "rated": 100,
            "watchLater": 50,
            "pass": 10,
            "remaining": 2840,
            "averageRating": 4.5
        }
    """
    return get_anime_for_rating_stats(current_user.id)


@router.get("/characters")
def get_characters_to_rate(
    limit: int = Query(50, ge=1, le=100, description="한 번에 가져올 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    캐릭터 평가 페이지 - 초고속 쿼리

    특징:
    - 평가한 애니의 캐릭터 중 미평가만
    - 랜덤성 내장 (매번 조금씩 다른 순서)
    - 단일 쿼리 최적화
    - 목표: 0.1초 이내

    Returns:
        {
            "items": [...],
            "limit": 50,
            "offset": 0,
            "has_more": true
        }
    """
    items = get_characters_for_rating(current_user.id, limit, offset)

    return {
        'items': items,
        'limit': limit,
        'offset': offset,
        'has_more': len(items) == limit
    }


@router.get("/characters/stats")
def get_character_rating_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    캐릭터 평가 통계

    Returns:
        {
            "total": 500,
            "rated": 50,
            "wantToKnow": 20,
            "notInterested": 5,
            "remaining": 425,
            "averageRating": 4.3
        }
    """
    return get_characters_for_rating_stats(current_user.id)
