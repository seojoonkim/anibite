"""
Rating Page Service - Ultra-optimized queries for rating pages
평가 페이지 전용 초고속 쿼리 (목표: 0.1초 이내)
"""
from typing import List, Dict
from database import db, dict_from_row


def get_anime_for_rating(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    애니메이션 평가 페이지 전용 - 초고속 쿼리

    최적화:
    - 서브쿼리 0개
    - LEFT JOIN으로 user_rating_status만 확인
    - site stats 제거 (불필요)
    - 가중치 랜덤 정렬: 인기도 기반 + 랜덤 변동 (대체로 인기작이 앞에)
    - 인덱스 활용

    목표: 0.1초 이내
    """

    rows = db.execute_query(
        """
        SELECT
            a.id,
            a.title_romaji,
            a.title_english,
            a.title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url,
            a.format,
            a.episodes,
            a.season,
            a.season_year,
            a.average_score,
            ur.status as user_rating_status
        FROM anime a
        LEFT JOIN user_ratings ur ON a.id = ur.anime_id AND ur.user_id = ?
        WHERE ur.id IS NULL OR ur.status = 'WANT_TO_WATCH'
        ORDER BY (a.popularity + ABS(RANDOM() % 2000)) DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    return [dict_from_row(row) for row in rows]


def get_characters_for_rating(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    캐릭터 평가 페이지 전용 - 초고속 쿼리

    최적화:
    - 단일 쿼리로 단순화
    - CTE 제거
    - 평가한 애니의 캐릭터 중 미평가만
    - 가중치 랜덤 정렬: 인기도 기반 + 랜덤 변동 (대체로 인기 캐릭터가 앞에)
    - 인덱스 활용

    목표: 0.1초 이내
    """

    rows = db.execute_query(
        """
        SELECT
            c.id,
            c.name_full,
            c.name_native,
            COALESCE('/' || c.image_local, c.image_url) as image_url,
            c.gender,
            c.favourites,
            ac.role,
            a.id as anime_id,
            COALESCE(a.title_korean, a.title_romaji) as anime_title,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as anime_cover
        FROM character c
        INNER JOIN anime_character ac ON c.id = ac.character_id
        INNER JOIN anime a ON ac.anime_id = a.id
        INNER JOIN user_ratings ur ON a.id = ur.anime_id AND ur.user_id = ? AND ur.status = 'RATED'
        LEFT JOIN character_ratings cr ON c.id = cr.character_id AND cr.user_id = ?
        WHERE cr.id IS NULL
            AND ac.role IN ('MAIN', 'SUPPORTING')
            AND c.name_full NOT LIKE '%Narrator%'
            AND c.name_full NOT LIKE '%Unknown%'
            AND c.name_full NOT LIKE '%Extra%'
            AND c.name_full NOT LIKE '%Background%'
        GROUP BY c.id
        ORDER BY (c.favourites + ABS(RANDOM() % 500)) DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, user_id, limit, offset)
    )

    return [dict_from_row(row) for row in rows]


def get_anime_for_rating_stats(user_id: int) -> Dict:
    """
    애니메이션 평가 페이지 통계 - 빠른 집계
    """

    row = db.execute_query(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN ur.status = 'RATED' THEN 1 ELSE 0 END) as rated,
            SUM(CASE WHEN ur.status = 'WANT_TO_WATCH' THEN 1 ELSE 0 END) as watch_later,
            SUM(CASE WHEN ur.status = 'PASS' THEN 1 ELSE 0 END) as pass,
            AVG(CASE WHEN ur.status = 'RATED' AND ur.rating IS NOT NULL THEN ur.rating END) as average_rating
        FROM user_ratings ur
        WHERE ur.user_id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    stats = dict_from_row(row) if row else {}

    # Total anime count (cached value)
    total_anime = db.execute_query(
        "SELECT COUNT(*) as cnt FROM anime",
        fetch_one=True
    )['cnt']

    return {
        'total': total_anime,
        'rated': stats.get('rated', 0),
        'watchLater': stats.get('watch_later', 0),
        'pass': stats.get('pass', 0),
        'remaining': total_anime - stats.get('rated', 0) - stats.get('pass', 0),
        'averageRating': stats.get('average_rating', 0) or 0
    }


def get_characters_for_rating_stats(user_id: int) -> Dict:
    """
    캐릭터 평가 페이지 통계 - 빠른 집계
    """

    row = db.execute_query(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN cr.status = 'RATED' THEN 1 ELSE 0 END) as rated,
            SUM(CASE WHEN cr.status = 'WANT_TO_KNOW' THEN 1 ELSE 0 END) as want_to_know,
            SUM(CASE WHEN cr.status = 'NOT_INTERESTED' THEN 1 ELSE 0 END) as not_interested,
            AVG(CASE WHEN cr.status = 'RATED' AND cr.rating IS NOT NULL THEN cr.rating END) as average_rating
        FROM character_ratings cr
        WHERE cr.user_id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    stats = dict_from_row(row) if row else {}

    # Available characters (from rated anime)
    available = db.execute_query(
        """
        SELECT COUNT(DISTINCT c.id) as cnt
        FROM character c
        INNER JOIN anime_character ac ON c.id = ac.character_id
        INNER JOIN user_ratings ur ON ac.anime_id = ur.anime_id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
            AND ac.role IN ('MAIN', 'SUPPORTING')
        """,
        (user_id,),
        fetch_one=True
    )['cnt']

    return {
        'total': available,
        'rated': stats.get('rated', 0),
        'wantToKnow': stats.get('want_to_know', 0),
        'notInterested': stats.get('not_interested', 0),
        'remaining': available - stats.get('rated', 0) - stats.get('not_interested', 0),
        'averageRating': stats.get('average_rating', 0) or 0
    }


def get_items_for_review_writing(user_id: int, limit: int = 50) -> List[Dict]:
    """
    리뷰 작성 페이지 전용 - 초고속 쿼리 (0.1초 목표)

    최적화:
    - activities 테이블 사용 (이미 denormalized)
    - UNION으로 애니+캐릭터 한번에
    - 리뷰 없는 항목만 (review_content IS NULL OR = '')
    - popularity 기반 정렬 + 랜덤성 내장
    - 단일 쿼리로 2개 API 호출 제거
    """

    rows = db.execute_query(
        """
        WITH combined AS (
            SELECT
                'anime' as type,
                item_id,
                user_id,
                rating,
                activity_time as updated_at,
                item_title,
                item_title_korean,
                item_image,
                item_year,
                NULL as anime_id,
                NULL as anime_title,
                NULL as anime_title_korean
            FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating'
            AND (review_content IS NULL OR review_content = '')

            UNION ALL

            SELECT
                'character' as type,
                item_id,
                user_id,
                rating,
                activity_time as updated_at,
                item_title,
                item_title_korean,
                item_image,
                NULL as item_year,
                anime_id,
                anime_title,
                anime_title_korean
            FROM activities
            WHERE user_id = ? AND activity_type = 'character_rating'
            AND (review_content IS NULL OR review_content = '')
        )
        SELECT *
        FROM combined
        ORDER BY ABS(RANDOM() % 100) DESC, updated_at DESC
        LIMIT ?
        """,
        (user_id, user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_review_writing_stats(user_id: int) -> Dict:
    """
    리뷰 작성 페이지 통계 - 초고속 집계
    """

    # 단일 쿼리로 모든 통계 계산
    stats = db.execute_query(
        """
        SELECT
            SUM(CASE WHEN activity_type = 'anime_rating'
                AND (review_content IS NOT NULL AND review_content != '')
                THEN 1 ELSE 0 END) as anime_reviewed,
            SUM(CASE WHEN activity_type = 'anime_rating'
                AND (review_content IS NULL OR review_content = '')
                THEN 1 ELSE 0 END) as anime_pending,
            SUM(CASE WHEN activity_type = 'character_rating'
                AND (review_content IS NOT NULL AND review_content != '')
                THEN 1 ELSE 0 END) as character_reviewed,
            SUM(CASE WHEN activity_type = 'character_rating'
                AND (review_content IS NULL OR review_content = '')
                THEN 1 ELSE 0 END) as character_pending
        FROM activities
        WHERE user_id = ? AND activity_type IN ('anime_rating', 'character_rating')
        """,
        (user_id,),
        fetch_one=True
    )

    result = dict_from_row(stats) if stats else {}

    return {
        'anime': {
            'reviewed': result.get('anime_reviewed', 0),
            'pending': result.get('anime_pending', 0)
        },
        'character': {
            'reviewed': result.get('character_reviewed', 0),
            'pending': result.get('character_pending', 0)
        },
        'total': {
            'reviewed': result.get('anime_reviewed', 0) + result.get('character_reviewed', 0),
            'pending': result.get('anime_pending', 0) + result.get('character_pending', 0)
        }
    }
