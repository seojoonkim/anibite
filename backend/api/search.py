"""
Unified Search API - Public search for anime and characters
통합 검색 API - 애니메이션과 캐릭터 동시 검색
"""
from fastapi import APIRouter, Query
from typing import Optional
from database import db

router = APIRouter()


@router.get("/")
def unified_search(
    q: str = Query(..., min_length=1, description="검색어"),
    sort: str = Query("popularity_desc", description="정렬 기준"),
    limit: int = Query(20, ge=1, le=50, description="결과 개수")
):
    """
    통합 검색 - 애니메이션과 캐릭터를 동시에 검색

    sort options:
    - popularity_desc: 인기순 (기본)
    - rating_desc: 평점 높은순
    - rating_asc: 평점 낮은순
    - title_asc: 제목순
    """
    results = {"anime": [], "characters": []}
    pattern = f"%{q}%"

    # 애니메이션 검색
    anime_order = {
        "popularity_desc": "popularity DESC",
        "rating_desc": "COALESCE(site_average_rating, average_score, 0) DESC",
        "rating_asc": "COALESCE(site_average_rating, average_score, 0) ASC",
        "title_asc": "COALESCE(title_korean, title_romaji, title_english) ASC",
    }.get(sort, "popularity DESC")

    anime_query = f"""
        SELECT
            id, title_korean, title_romaji, title_english, title_native,
            COALESCE(cover_image_url, cover_image_local) as cover_image,
            format, episodes, status, season_year,
            COALESCE(site_average_rating, average_score) as rating,
            site_rating_count, popularity
        FROM anime
        WHERE title_korean LIKE ?
           OR title_romaji LIKE ?
           OR title_english LIKE ?
           OR title_native LIKE ?
        ORDER BY {anime_order}
        LIMIT ?
    """
    anime_results = db.execute_query(
        anime_query,
        (pattern, pattern, pattern, pattern, limit)
    )

    results["anime"] = [
        {
            "id": row[0],
            "title_korean": row[1],
            "title_romaji": row[2],
            "title_english": row[3],
            "title_native": row[4],
            "cover_image": row[5],
            "format": row[6],
            "episodes": row[7],
            "status": row[8],
            "season_year": row[9],
            "rating": row[10],
            "rating_count": row[11],
            "popularity": row[12]
        }
        for row in anime_results
    ]

    # 캐릭터 검색
    char_order = {
        "popularity_desc": "c.favourites DESC",
        "rating_desc": "COALESCE(c.site_average_rating, 0) DESC",
        "rating_asc": "COALESCE(c.site_average_rating, 0) ASC",
        "title_asc": "COALESCE(c.name_korean, c.name_full) ASC",
    }.get(sort, "c.favourites DESC")

    char_query = f"""
        SELECT
            c.id, c.name_korean, c.name_full, c.name_native,
            COALESCE(c.image_url, c.image_local) as image_large,
            c.favourites,
            c.site_average_rating,
            c.site_rating_count,
            a.id as anime_id,
            a.title_korean as anime_title_korean,
            a.title_romaji as anime_title_romaji
        FROM character c
        LEFT JOIN anime_character ac ON c.id = ac.character_id
        LEFT JOIN anime a ON ac.anime_id = a.id
        WHERE c.name_korean LIKE ?
           OR c.name_full LIKE ?
           OR c.name_native LIKE ?
        GROUP BY c.id
        ORDER BY {char_order}
        LIMIT ?
    """
    char_results = db.execute_query(
        char_query,
        (pattern, pattern, pattern, limit)
    )

    results["characters"] = [
        {
            "id": row[0],
            "name_korean": row[1],
            "name_full": row[2],
            "name_native": row[3],
            "image_large": row[4],
            "favourites": row[5],
            "rating": row[6],
            "rating_count": row[7],
            "anime_id": row[8],
            "anime_title_korean": row[9],
            "anime_title_romaji": row[10]
        }
        for row in char_results
    ]

    return results
