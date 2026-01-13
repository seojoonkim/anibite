"""
User API Router
사용자 프로필, 통계
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import List, Dict
import os
import shutil
from pathlib import Path
from models.user import UserResponse, UserProfileResponse, UserStatsResponse, UserUpdate, PasswordUpdate
from services.profile_service import (
    get_user_profile,
    get_user_stats,
    get_genre_preferences,
    get_rating_distribution,
    get_watch_history,
    get_watch_time,
    get_year_distribution,
    get_format_distribution,
    get_episode_length_distribution,
    get_rating_stats,
    get_studio_stats,
    get_season_stats,
    get_genre_combination_stats,
    get_five_star_characters,
    get_leaderboard,
    get_studio_preferences,
    get_hidden_gems,
    get_source_preferences,
    get_director_preferences,
    get_genre_radar_data
)
from services.auth_service import update_user_profile, update_user_password, update_user_avatar
from api.deps import get_current_user

router = APIRouter()


@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    내 프로필 조회

    사용자 정보 + 통계 (오타쿠 점수, 평점 통계 등)
    """
    profile = get_user_profile(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.put("/me/profile", response_model=UserResponse)
def update_my_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 프로필 업데이트

    표시 이름, 이메일 변경
    """
    return update_user_profile(
        current_user.id,
        display_name=update_data.display_name,
        email=update_data.email
    )


@router.put("/me/password")
def update_my_password(
    password_data: PasswordUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    비밀번호 변경

    현재 비밀번호 확인 후 변경
    """
    update_user_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    return {"message": "Password updated successfully"}


@router.get("/me/stats", response_model=UserStatsResponse)
def get_my_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    내 통계 조회

    오타쿠 점수, 평가 수, 시청 시간 등
    """
    stats = get_user_stats(current_user.id)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stats not found"
        )
    return stats


@router.get("/me/genre-preferences", response_model=List[Dict])
def get_my_genre_preferences(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내 장르 선호도

    평가한 애니메이션의 장르별 평균 평점
    최소 3개 이상 평가한 장르만 포함
    """
    return get_genre_preferences(current_user.id, limit)


@router.get("/me/rating-distribution", response_model=List[Dict])
def get_my_rating_distribution(current_user: UserResponse = Depends(get_current_user)):
    """
    내 평점 분포

    각 평점별 애니메이션 개수
    """
    return get_rating_distribution(current_user.id)


@router.get("/me/watch-history", response_model=List[Dict])
def get_my_watch_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    최근 평가한 애니메이션

    최신순으로 정렬
    """
    return get_watch_history(current_user.id, limit)


@router.get("/me/watch-time", response_model=Dict)
def get_my_watch_time(current_user: UserResponse = Depends(get_current_user)):
    """
    시청 시간 조회

    평가한 애니메이션의 총 재생시간 (분, 시간, 일)
    """
    return get_watch_time(current_user.id)


@router.get("/me/year-distribution", response_model=List[Dict])
def get_my_year_distribution(current_user: UserResponse = Depends(get_current_user)):
    """
    연도별 시청 분포

    사용자가 평가한 애니메이션들의 방영 연도별 분포
    """
    return get_year_distribution(current_user.id)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile_by_id(user_id: int):
    """
    다른 사용자 프로필 조회 (공개)

    사용자 정보 + 통계
    """
    profile = get_user_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return profile


@router.get("/{user_id}/genre-preferences", response_model=List[Dict])
def get_user_genre_preferences(
    user_id: int,
    limit: int = Query(10, ge=1, le=50)
):
    """
    다른 사용자의 장르 선호도 (공개)
    """
    return get_genre_preferences(user_id, limit)


@router.get("/me/format-distribution", response_model=List[Dict])
def get_my_format_distribution(current_user: UserResponse = Depends(get_current_user)):
    """
    포맷별 분포 (TV, MOVIE, OVA 등)

    평가한 애니메이션의 포맷별 개수와 평균 평점
    """
    return get_format_distribution(current_user.id)


@router.get("/me/episode-length-distribution", response_model=List[Dict])
def get_my_episode_length_distribution(current_user: UserResponse = Depends(get_current_user)):
    """
    에피소드 길이별 분포 (단편/중편/장편)

    - SHORT: 1-12화
    - MEDIUM: 13-26화
    - LONG: 27화 이상
    """
    return get_episode_length_distribution(current_user.id)


@router.get("/me/rating-stats", response_model=Dict)
def get_my_rating_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    평점 통계

    평균, 표준편차, 최소값, 최대값
    """
    return get_rating_stats(current_user.id)


@router.get("/me/studio-stats", response_model=List[Dict])
def get_my_studio_stats(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    스튜디오별 통계

    가장 많이 본 스튜디오와 평균 평점
    최소 2개 이상 평가한 스튜디오만 포함
    """
    return get_studio_stats(current_user.id, limit)


@router.get("/me/season-stats", response_model=List[Dict])
def get_my_season_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    시즌별 통계 (봄/여름/가을/겨울)

    각 시즌에 방영된 애니메이션 개수와 평균 평점
    """
    return get_season_stats(current_user.id)


@router.get("/me/genre-combinations", response_model=List[Dict])
def get_my_genre_combinations(
    limit: int = Query(10, ge=1, le=20),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    장르 조합 분석

    가장 많이 본 2개 장르 조합
    최소 2개 이상 평가한 조합만 포함
    """
    return get_genre_combination_stats(current_user.id, limit)


@router.get("/me/five-star-characters", response_model=List[Dict])
def get_my_five_star_characters(current_user: UserResponse = Depends(get_current_user)):
    """
    5점 평가한 캐릭터 목록

    프로필 사진 선택에 사용
    """
    return get_five_star_characters(current_user.id)


@router.get("/me/character-ratings", response_model=List[Dict])
def get_my_character_ratings(
    limit: int = Query(500, ge=1, le=1000),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    내가 평가한 캐릭터 목록

    rating, status와 함께 반환
    """
    from services.profile_service import get_character_ratings
    return get_character_ratings(current_user.id, limit)


@router.post("/me/avatar/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    프로필 사진 업로드

    이미지 파일을 업로드하고 avatar_url 업데이트
    """
    # 업로드 디렉토리 생성
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 파일 확장자 검증
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 파일명 생성 (user_id + 확장자)
    filename = f"{current_user.id}{file_extension}"
    file_path = upload_dir / filename

    # 기존 파일 삭제
    for ext in allowed_extensions:
        old_file = upload_dir / f"{current_user.id}{ext}"
        if old_file.exists():
            old_file.unlink()

    # 파일 저장
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # avatar_url 업데이트
    avatar_url = f"/uploads/avatars/{filename}"
    update_user_avatar(current_user.id, avatar_url)

    return {"avatar_url": avatar_url}


@router.put("/me/avatar/character")
def set_avatar_from_character(
    character_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    캐릭터 이미지를 프로필 사진으로 설정

    5점 평가한 캐릭터만 선택 가능
    """
    # 5점 캐릭터 목록에서 확인
    five_star_chars = get_five_star_characters(current_user.id)
    char_ids = [c['character_id'] for c in five_star_chars]

    if character_id not in char_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only set avatar from 5-star rated characters"
        )

    # 캐릭터 이미지 URL 가져오기
    char = next((c for c in five_star_chars if c['character_id'] == character_id), None)
    if not char:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 캐릭터의 원래 image_url 가져오기 (외부 URL)
    # 프론트엔드에서 R2 우선 시도하고 실패하면 이 URL로 fallback
    avatar_url = char.get('image_url') or char.get('image_local')
    if not avatar_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character has no image"
        )

    # avatar_url 업데이트
    update_user_avatar(current_user.id, avatar_url)

    # character_id도 함께 반환 (프론트엔드에서 R2 우선 시도용)
    return {
        "avatar_url": avatar_url,
        "character_id": character_id
    }


@router.get("/leaderboard", response_model=List[Dict])
def get_users_leaderboard(
    limit: int = Query(50, ge=1, le=100)
):
    """
    사용자 리더보드

    오타쿠 점수 높은 순으로 정렬된 사용자 목록
    """
    return get_leaderboard(limit)


@router.get("/me/studio-preferences", response_model=Dict)
def get_my_studio_preferences(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    제작사 선호도 분석

    좋아하는 제작사 Top N과 평균 평점
    """
    return get_studio_preferences(current_user.id, limit)


@router.get("/me/director-preferences", response_model=List[Dict])
def get_my_director_preferences(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    감독 선호도 분석

    좋아하는 감독 Top N과 평균 평점
    """
    return get_director_preferences(current_user.id, limit)


@router.get("/me/hidden-gems", response_model=List[Dict])
def get_my_hidden_gems(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    숨겨진 보석 발견

    대중 평점은 낮지만 내가 높게 평가한 작품
    또는 과대평가라고 생각하는 작품
    """
    return get_hidden_gems(current_user.id, limit)


@router.get("/me/source-preferences", response_model=Dict)
def get_my_source_preferences(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    원작 매체별 선호도

    만화, 라노벨, 오리지널 등 원작 매체별 통계
    """
    return get_source_preferences(current_user.id)


@router.get("/me/genre-radar", response_model=Dict)
def get_my_genre_radar(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    장르 레이더 차트 데이터

    주요 장르별 평균 평점과 개수 (레이더 차트용)
    """
    return get_genre_radar_data(current_user.id)


@router.get("/{user_id}/character-ratings", response_model=List[Dict])
def get_user_character_ratings(
    user_id: int,
    limit: int = Query(500, ge=1, le=1000)
):
    """
    다른 사용자가 평가한 캐릭터 목록 (공개)

    rating, status와 함께 반환
    """
    from services.profile_service import get_character_ratings
    return get_character_ratings(user_id, limit)
