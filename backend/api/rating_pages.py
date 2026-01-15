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
    get_characters_for_rating_stats,
    get_items_for_review_writing,
    get_review_writing_stats
)
from api.deps import get_current_user

router = APIRouter()


@router.get("/anime")
def get_anime_to_rate(
    limit: int = Query(50, ge=1, le=200, description="한 번에 가져올 개수"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    애니메이션 평가 페이지 - 초고속 쿼리

    특징:
    - 미평가 + WANT_TO_WATCH 항목 반환
    - 매번 다른 랜덤 순서 (가중치 기반)
    - 서브쿼리 0개
    - 목표: 0.1초 이내
    - 프론트엔드에서 페이지네이션 처리

    Returns:
        {
            "items": [...],
            "total": 123
        }
    """
    items = get_anime_for_rating(current_user.id, limit)

    return {
        'items': items,
        'total': len(items)
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
    limit: int = Query(50, ge=1, le=200, description="한 번에 가져올 개수"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    캐릭터 평가 페이지 - 초고속 쿼리

    특징:
    - 평가한 애니의 캐릭터 중 미평가만
    - 매번 다른 랜덤 순서 (가중치 기반)
    - 단일 쿼리 최적화
    - 목표: 0.1초 이내
    - 프론트엔드에서 페이지네이션 처리

    Returns:
        {
            "items": [...],
            "total": 123
        }
    """
    items = get_characters_for_rating(current_user.id, limit)

    return {
        'items': items,
        'total': len(items)
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


@router.get("/write-reviews")
def get_items_for_reviews(
    limit: int = Query(50, ge=1, le=100, description="한 번에 가져올 개수"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    리뷰 작성 페이지 - 초고속 쿼리 (0.1초 목표)

    특징:
    - 애니메이션 + 캐릭터 통합 (단일 쿼리)
    - 리뷰 없는 항목만 반환
    - popularity 기반 정렬 + 랜덤성 내장
    - activities 테이블 사용으로 최적화

    Returns:
        {
            "items": [
                {
                    "type": "anime" | "character",
                    "item_id": 123,
                    "rating": 4.5,
                    "updated_at": "...",
                    "item_title": "...",
                    "item_title_korean": "...",
                    "item_image": "...",
                    "item_popularity": 1000,
                    "item_year": 2023
                },
                ...
            ]
        }
    """
    items = get_items_for_review_writing(current_user.id, limit)

    return {
        'items': items
    }


@router.get("/write-reviews/stats")
def get_review_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict:
    """
    리뷰 작성 통계

    Returns:
        {
            "anime": {
                "reviewed": 50,
                "pending": 30
            },
            "character": {
                "reviewed": 20,
                "pending": 15
            },
            "total": {
                "reviewed": 70,
                "pending": 45
            }
        }
    """
    return get_review_writing_stats(current_user.id)
