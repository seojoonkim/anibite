"""
Anime Service
애니메이션 조회, 검색, 필터링
"""
from typing import List, Optional, Dict
import random
from database import db, dict_from_row, dicts_from_rows
from models.anime import AnimeResponse, AnimeDetailResponse, AnimeListResponse
from config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def get_anime_list(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    genre: Optional[str] = None,
    season: Optional[str] = None,
    year: Optional[int] = None,
    format: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "popularity",
    exclude_user_id: Optional[int] = None
) -> AnimeListResponse:
    """애니메이션 목록 조회 (필터링, 페이지네이션)"""

    # 페이지 크기 제한
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    # 기본 쿼리
    where_clauses = []
    params = []

    # 필터 조건
    if genre:
        where_clauses.append("""
            id IN (
                SELECT anime_id FROM anime_genre ag
                JOIN genre g ON ag.genre_id = g.id
                WHERE g.name = ?
            )
        """)
        params.append(genre)

    if season:
        where_clauses.append("season = ?")
        params.append(season)

    if year:
        where_clauses.append("season_year = ?")
        params.append(year)

    if format:
        where_clauses.append("format = ?")
        params.append(format)

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    # 이미 평가한 항목 제외 (RATED, PASS 제외, WANT_TO_WATCH는 별도 처리)
    if exclude_user_id:
        where_clauses.append("""
            id NOT IN (
                SELECT anime_id FROM user_ratings
                WHERE user_id = ? AND status IN ('RATED', 'PASS', 'WANT_TO_WATCH')
            )
        """)
        params.append(exclude_user_id)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 정렬
    sort_column = {
        "popularity": "(popularity + (RANDOM() % 3000)) DESC",  # 랜덤성 추가
        "score": "average_score DESC",
        "trending": "trending DESC",
        "favourites": "favourites DESC",
        "title": "title_romaji ASC",
        "recent": "season_year DESC, season DESC"
    }.get(sort_by, "(popularity + (RANDOM() % 3000)) DESC")

    # 전체 개수 조회
    count_query = f"SELECT COUNT(*) as total FROM anime WHERE {where_clause}"
    total = db.execute_query(count_query, tuple(params), fetch_one=True)['total']

    # 목록 조회 (시즌 번호 포함, 로컬 이미지 우선, 우리 사이트 평가 통계, 사용자 평가 상태)
    user_status_query = ""
    if exclude_user_id:
        user_status_query = f"""
               ,(SELECT ur.status FROM user_ratings ur
                 WHERE ur.anime_id = a.id AND ur.user_id = {exclude_user_id}) as user_rating_status
        """

    list_query = f"""
        SELECT a.id, a.title_romaji, a.title_english, a.title_native, a.title_korean, a.title_korean_official,
               a.type, a.format, a.status, a.description,
               a.season, a.season_year, a.episodes, a.duration,
               COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
               a.cover_image_color, a.banner_image_url,
               a.average_score, a.popularity, a.favourites, a.source, a.is_adult,
               (SELECT COUNT(*) FROM anime_relation ar
                WHERE ar.anime_id = a.id AND ar.relation_type = 'PREQUEL') + 1 as season_number,
               (SELECT COUNT(*) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
               (SELECT AVG(ur.rating) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating
               {user_status_query}
        FROM anime a
        WHERE {where_clause}
        ORDER BY {sort_column}
        LIMIT ? OFFSET ?
    """

    # exclude_user_id가 있으면 WANT_TO_WATCH 3개를 섞어서 포함
    all_rows = []
    if exclude_user_id and page_size >= 3:
        # 1. 일반 애니메이션 (page_size - 3)개 가져오기
        regular_count = page_size - 3
        regular_rows = db.execute_query(list_query, tuple(params + [regular_count, offset]))
        all_rows.extend(regular_rows)

        # 2. WANT_TO_WATCH에서 3개 랜덤하게 가져오기
        watchlist_query = f"""
            SELECT a.id, a.title_romaji, a.title_english, a.title_native, a.title_korean, a.title_korean_official,
                   a.type, a.format, a.status, a.description,
                   a.season, a.season_year, a.episodes, a.duration,
                   COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
                   a.cover_image_color, a.banner_image_url,
                   a.average_score, a.popularity, a.favourites, a.source, a.is_adult,
                   (SELECT COUNT(*) FROM anime_relation ar
                    WHERE ar.anime_id = a.id AND ar.relation_type = 'PREQUEL') + 1 as season_number,
                   (SELECT COUNT(*) FROM user_ratings ur
                    WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
                   (SELECT AVG(ur.rating) FROM user_ratings ur
                    WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating,
                   'WANT_TO_WATCH' as user_rating_status
            FROM anime a
            WHERE a.id IN (
                SELECT anime_id FROM user_ratings
                WHERE user_id = ? AND status = 'WANT_TO_WATCH'
            )
            ORDER BY RANDOM()
            LIMIT 3
        """
        watchlist_rows = db.execute_query(watchlist_query, (exclude_user_id,))
        all_rows.extend(watchlist_rows)

        # 3. 섞기
        random.shuffle(all_rows)
    else:
        # exclude_user_id가 없거나 page_size가 작으면 기존 로직
        all_rows = db.execute_query(list_query, tuple(params + [page_size, offset]))

    # 각 애니메이션에 장르 정보 추가
    items = []
    for row in all_rows:
        anime_dict = dict_from_row(row)
        anime_dict['airing_status'] = anime_dict.get('status')  # airing_status 별칭 추가

        # 장르 가져오기
        genre_rows = db.execute_query(
            """
            SELECT g.name
            FROM anime_genre ag
            JOIN genre g ON ag.genre_id = g.id
            WHERE ag.anime_id = ?
            """,
            (anime_dict['id'],)
        )
        anime_dict['genres'] = [g['name'] for g in genre_rows]

        items.append(AnimeResponse(**anime_dict))

    return AnimeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total
    )


def get_anime_by_id(anime_id: int) -> Optional[AnimeDetailResponse]:
    """애니메이션 상세 정보 조회"""

    # 기본 정보 (로컬 이미지 우선)
    anime_row = db.execute_query(
        """
        SELECT id, title_romaji, title_english, title_native, title_korean, title_korean_official,
               type, format, status, description,
               season, season_year, episodes, duration,
               start_date, end_date,
               COALESCE('/' || cover_image_local, cover_image_url) as cover_image_url,
               cover_image_color, banner_image_url,
               average_score, popularity, favourites, trending,
               source, country_of_origin, is_adult, is_licensed,
               site_url, trailer_url, trailer_site
        FROM anime WHERE id = ?
        """,
        (anime_id,),
        fetch_one=True
    )

    if anime_row is None:
        return None

    anime_dict = dict_from_row(anime_row)

    # 장르
    genre_rows = db.execute_query(
        """
        SELECT g.name
        FROM anime_genre ag
        JOIN genre g ON ag.genre_id = g.id
        WHERE ag.anime_id = ?
        """,
        (anime_id,)
    )
    anime_dict['genres'] = [row['name'] for row in genre_rows]

    # 태그 (상위 10개)
    tag_rows = db.execute_query(
        """
        SELECT t.id, t.name, t.description, t.category, at.rank, at.is_spoiler
        FROM anime_tag at
        JOIN tag t ON at.tag_id = t.id
        WHERE at.anime_id = ?
        ORDER BY at.rank DESC
        LIMIT 10
        """,
        (anime_id,)
    )
    anime_dict['tags'] = [dict_from_row(row) for row in tag_rows]

    # 스튜디오
    studio_rows = db.execute_query(
        """
        SELECT s.id, s.name, s.is_animation_studio, ast.is_main
        FROM anime_studio ast
        JOIN studio s ON ast.studio_id = s.id
        WHERE ast.anime_id = ?
        ORDER BY ast.is_main DESC
        """,
        (anime_id,)
    )
    anime_dict['studios'] = [dict_from_row(row) for row in studio_rows]

    # 캐릭터 & 성우 (상위 12명)
    character_rows = db.execute_query(
        """
        SELECT
            c.id as character_id,
            c.name_full as character_name,
            c.name_korean as character_name_korean,
            c.image_url as character_image,
            ac.role as character_role,
            s.id as voice_actor_id,
            s.name_full as voice_actor_name,
            s.image_url as voice_actor_image
        FROM anime_character ac
        JOIN character c ON ac.character_id = c.id
        LEFT JOIN character_voice_actor cva ON cva.character_id = c.id AND cva.anime_id = ac.anime_id
        LEFT JOIN staff s ON cva.staff_id = s.id
        WHERE ac.anime_id = ?
        ORDER BY
            CASE ac.role
                WHEN 'MAIN' THEN 1
                WHEN 'SUPPORTING' THEN 2
                ELSE 3
            END,
            c.favourites DESC
        LIMIT 12
        """,
        (anime_id,)
    )
    anime_dict['characters'] = [dict_from_row(row) for row in character_rows]

    # 스태프 (감독, 각본 등 - 상위 10명)
    staff_rows = db.execute_query(
        """
        SELECT
            s.id,
            s.name_full,
            s.image_url,
            ast.role
        FROM anime_staff ast
        JOIN staff s ON ast.staff_id = s.id
        WHERE ast.anime_id = ?
        ORDER BY
            CASE
                WHEN ast.role LIKE '%Director%' THEN 1
                WHEN ast.role LIKE '%Writer%' THEN 2
                WHEN ast.role LIKE '%Music%' THEN 3
                ELSE 4
            END,
            s.favourites DESC
        LIMIT 10
        """,
        (anime_id,)
    )
    anime_dict['staff'] = [dict_from_row(row) for row in staff_rows]

    # 추천 애니메이션 (상위 6개)
    recommendation_rows = db.execute_query(
        """
        SELECT
            a.id,
            a.title_romaji,
            a.title_english,
            a.title_korean,
            a.title_korean_official,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
            a.average_score,
            ar.rating as recommendation_score,
            (SELECT COUNT(*) FROM user_ratings ur
             WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
            (SELECT AVG(ur.rating) FROM user_ratings ur
             WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating
        FROM anime_recommendation ar
        JOIN anime a ON ar.recommended_anime_id = a.id
        WHERE ar.anime_id = ?
        ORDER BY ar.rating DESC
        LIMIT 6
        """,
        (anime_id,)
    )
    anime_dict['recommendations'] = [dict_from_row(row) for row in recommendation_rows]

    # 외부 링크 (스트리밍 사이트 등)
    external_link_rows = db.execute_query(
        """
        SELECT site, url, type, language
        FROM anime_external_link
        WHERE anime_id = ?
        ORDER BY
            CASE type
                WHEN 'STREAMING' THEN 1
                WHEN 'INFO' THEN 2
                ELSE 3
            END
        """,
        (anime_id,)
    )
    anime_dict['external_links'] = [dict_from_row(row) for row in external_link_rows]

    # 우리 사이트 평가 통계
    site_stats_row = db.execute_query(
        """
        SELECT
            COUNT(*) as rating_count,
            AVG(rating) as average_rating
        FROM user_ratings
        WHERE anime_id = ? AND status = 'RATED' AND rating IS NOT NULL
        """,
        (anime_id,),
        fetch_one=True
    )
    anime_dict['site_rating_count'] = site_stats_row['rating_count'] if site_stats_row else 0
    anime_dict['site_average_rating'] = site_stats_row['average_rating'] if site_stats_row else None

    # 우리 사이트 평점 분포 (0.5 단위)
    rating_dist_rows = db.execute_query(
        """
        SELECT
            rating,
            COUNT(*) as count
        FROM user_ratings
        WHERE anime_id = ? AND status = 'RATED' AND rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating DESC
        """,
        (anime_id,)
    )
    anime_dict['site_rating_distribution'] = [dict_from_row(row) for row in rating_dist_rows]

    return AnimeDetailResponse(**anime_dict)


def search_anime(
    query: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE
) -> AnimeListResponse:
    """애니메이션 검색 (제목 기반, 띄어쓰기 무시)"""

    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    # 띄어쓰기 제거한 검색 패턴
    search_pattern = f"%{query.replace(' ', '')}%"

    # 전체 개수 (띄어쓰기 무시)
    total = db.execute_query(
        """
        SELECT COUNT(*) as total FROM anime
        WHERE REPLACE(title_romaji, ' ', '') LIKE ?
           OR REPLACE(title_english, ' ', '') LIKE ?
           OR REPLACE(title_native, ' ', '') LIKE ?
           OR REPLACE(title_korean, ' ', '') LIKE ?
        """,
        (search_pattern, search_pattern, search_pattern, search_pattern),
        fetch_one=True
    )['total']

    # 검색 결과 (로컬 이미지 우선, 우리 사이트 평가 통계, 띄어쓰기 무시)
    rows = db.execute_query(
        """
        SELECT a.id, a.title_romaji, a.title_english, a.title_native, a.title_korean, a.title_korean_official,
               a.type, a.format, a.status, a.description,
               a.season, a.season_year, a.episodes, a.duration,
               COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
               a.cover_image_color, a.banner_image_url,
               a.average_score, a.popularity, a.favourites, a.source, a.is_adult,
               (SELECT COUNT(*) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
               (SELECT AVG(ur.rating) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating
        FROM anime a
        WHERE REPLACE(a.title_romaji, ' ', '') LIKE ?
           OR REPLACE(a.title_english, ' ', '') LIKE ?
           OR REPLACE(a.title_native, ' ', '') LIKE ?
           OR REPLACE(a.title_korean, ' ', '') LIKE ?
        ORDER BY a.popularity DESC
        LIMIT ? OFFSET ?
        """,
        (search_pattern, search_pattern, search_pattern, search_pattern, page_size, offset)
    )

    items = [AnimeResponse(**dict_from_row(row)) for row in rows]

    return AnimeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total
    )


def get_popular_anime(limit: int = 50) -> List[AnimeResponse]:
    """인기 애니메이션 (인기도 순)"""

    rows = db.execute_query(
        """
        SELECT a.id, a.title_romaji, a.title_english, a.title_native, a.title_korean, a.title_korean_official,
               a.type, a.format, a.status, a.description,
               a.season, a.season_year, a.episodes, a.duration,
               COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
               a.cover_image_color, a.banner_image_url,
               a.average_score, a.popularity, a.favourites, a.source, a.is_adult,
               (SELECT COUNT(*) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
               (SELECT AVG(ur.rating) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating
        FROM anime a
        ORDER BY a.popularity DESC
        LIMIT ?
        """,
        (limit,)
    )

    return [AnimeResponse(**dict_from_row(row)) for row in rows]


def get_top_rated_anime(limit: int = 50) -> List[AnimeResponse]:
    """최고 평점 애니메이션"""

    rows = db.execute_query(
        """
        SELECT a.id, a.title_romaji, a.title_english, a.title_native, a.title_korean, a.title_korean_official,
               a.type, a.format, a.status, a.description,
               a.season, a.season_year, a.episodes, a.duration,
               COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
               a.cover_image_color, a.banner_image_url,
               a.average_score, a.popularity, a.favourites, a.source, a.is_adult,
               (SELECT COUNT(*) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_rating_count,
               (SELECT AVG(ur.rating) FROM user_ratings ur
                WHERE ur.anime_id = a.id AND ur.status = 'RATED' AND ur.rating IS NOT NULL) as site_average_rating
        FROM anime a
        WHERE a.average_score IS NOT NULL
        ORDER BY a.average_score DESC, a.popularity DESC
        LIMIT ?
        """,
        (limit,)
    )

    return [AnimeResponse(**dict_from_row(row)) for row in rows]


def get_all_genres() -> List[str]:
    """모든 장르 목록"""
    rows = db.execute_query("SELECT name FROM genre ORDER BY name")
    return [row['name'] for row in rows]
