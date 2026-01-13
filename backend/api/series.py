"""
Series API Router
시리즈 관계 조회 및 일괄 처리
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from models.user import UserResponse
from services.series_service import get_series_info
from services.rating_service import create_or_update_rating
from models.rating import RatingCreate, RatingStatus
from api.deps import get_current_user

router = APIRouter()


class BulkRatingRequest(BaseModel):
    anime_ids: List[int]
    status: RatingStatus


@router.get("/anime/{anime_id}/sequels")
def get_anime_sequels(
    anime_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    애니메이션의 후속작 정보 조회
    """
    series_info = get_series_info(anime_id)
    if not series_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    return series_info


@router.post("/bulk-rate")
def bulk_rate_series(
    request: BulkRatingRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    시리즈 일괄 평가 처리
    """
    results = []
    errors = []

    for anime_id in request.anime_ids:
        try:
            rating_data = RatingCreate(
                anime_id=anime_id,
                status=request.status,
                rating=None  # 상태만 변경
            )
            result = create_or_update_rating(current_user.id, rating_data)
            results.append(result)
        except Exception as e:
            errors.append({
                'anime_id': anime_id,
                'error': str(e)
            })

    return {
        'success_count': len(results),
        'error_count': len(errors),
        'results': results,
        'errors': errors
    }
