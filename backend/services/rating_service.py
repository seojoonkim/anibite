"""
Rating Service
평점 생성, 수정, 삭제, 조회
"""
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException, status
from database import db, dict_from_row, dicts_from_rows
from models.rating import RatingCreate, RatingUpdate, RatingResponse, UserRatingListResponse, RatingStatus


def create_or_update_rating(user_id: int, rating_data: RatingCreate) -> RatingResponse:
    """평점 생성 또는 수정"""

    # 애니메이션 존재 확인
    anime_exists = db.execute_query(
        "SELECT id FROM anime WHERE id = ?",
        (rating_data.anime_id,),
        fetch_one=True
    )

    if not anime_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )

    # 기존 평점 확인
    existing = db.execute_query(
        "SELECT id FROM user_ratings WHERE user_id = ? AND anime_id = ?",
        (user_id, rating_data.anime_id),
        fetch_one=True
    )

    # Delete from activities first (트리거가 동작하지 않을 경우를 대비)
    db.execute_update(
        """
        DELETE FROM activities
        WHERE activity_type = 'anime_rating'
          AND user_id = ?
          AND item_id = ?
        """,
        (user_id, rating_data.anime_id)
    )

    if existing:
        # 수정
        # WANT_TO_WATCH 또는 PASS로 변경 시 rating을 NULL로 설정
        final_rating = rating_data.rating if rating_data.status == RatingStatus.RATED else None

        db.execute_update(
            """
            UPDATE user_ratings
            SET rating = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND anime_id = ?
            """,
            (final_rating, rating_data.status.value, user_id, rating_data.anime_id)
        )
        rating_id = existing['id']
    else:
        # 생성
        # WANT_TO_WATCH 또는 PASS일 때는 rating을 NULL로 설정
        final_rating = rating_data.rating if rating_data.status == RatingStatus.RATED else None

        rating_id = db.execute_insert(
            """
            INSERT INTO user_ratings (user_id, anime_id, rating, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (user_id, rating_data.anime_id, final_rating, rating_data.status.value)
        )

    # RATED 상태일 때만 activities에 추가 (트리거가 동작하지 않을 경우를 대비)
    if rating_data.status == RatingStatus.RATED and rating_data.rating:
        _sync_to_activities(user_id, rating_data.anime_id)

    # 사용자 통계 업데이트
    _update_user_stats(user_id)

    # 생성/수정된 평점 조회
    return get_rating_by_id(rating_id)


def get_rating_by_id(rating_id: int) -> Optional[RatingResponse]:
    """평점 ID로 조회"""
    row = db.execute_query(
        """
        SELECT ur.*, a.title_romaji as anime_title, a.cover_image_url as anime_cover_image
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.id = ?
        """,
        (rating_id,),
        fetch_one=True
    )

    if row is None:
        return None

    return RatingResponse(**dict_from_row(row))


def get_user_rating_for_anime(user_id: int, anime_id: int) -> Optional[RatingResponse]:
    """특정 애니메이션에 대한 사용자 평점 조회"""
    row = db.execute_query(
        """
        SELECT ur.*, a.title_romaji as anime_title, a.cover_image_url as anime_cover_image
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.anime_id = ?
        """,
        (user_id, anime_id),
        fetch_one=True
    )

    if row is None:
        return None

    return RatingResponse(**dict_from_row(row))


def get_user_ratings(
    user_id: int,
    status_filter: Optional[RatingStatus] = None,
    limit: Optional[int] = None,
    without_review: bool = False
) -> UserRatingListResponse:
    """사용자의 모든 평점 조회 (activities 테이블 사용으로 최적화)"""

    # activities는 RATED 상태만 저장하므로, 다른 status는 원본 테이블 사용
    if status_filter and status_filter != RatingStatus.RATED:
        # WANT_TO_WATCH, PASS 등은 user_ratings 테이블에서 직접 조회
        where_clause = "ur.user_id = ? AND ur.status = ?"
        params = [user_id, status_filter.value]

        total = db.execute_query(
            f"SELECT COUNT(*) as total FROM user_ratings ur WHERE {where_clause}",
            tuple(params),
            fetch_one=True
        )['total']

        limit_clause = f"LIMIT {limit}" if limit else ""
        rows = db.execute_query(
            f"""
            SELECT
                ur.*,
                a.title_romaji,
                a.title_english,
                a.title_korean,
                a.cover_image_url as image_url,
                a.season_year,
                a.episodes
            FROM user_ratings ur
            JOIN anime a ON ur.anime_id = a.id
            WHERE {where_clause}
            ORDER BY ur.updated_at DESC
            {limit_clause}
            """,
            tuple(params)
        )

        items = [RatingResponse(**dict_from_row(row)) for row in rows]

        # WANT_TO_WATCH, PASS는 평균 평점이 없음
        return UserRatingListResponse(
            items=items,
            total=total,
            average_rating=None
        )

    # RATED 또는 필터 없음: activities 테이블에서 조회
    # Check if we should filter items without reviews (for WriteReviews page)
    if without_review:
        # 리뷰가 없는 항목만: review_content가 NULL이거나 빈 문자열인 것
        total = db.execute_query(
            """
            SELECT COUNT(*) as total FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating'
            AND (review_content IS NULL OR review_content = '')
            """,
            (user_id,),
            fetch_one=True
        )['total']

        # 평균 평점 (리뷰 없는 항목들의)
        avg_row = db.execute_query(
            """
            SELECT AVG(rating) as avg_rating
            FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating' AND rating IS NOT NULL
            AND (review_content IS NULL OR review_content = '')
            """,
            (user_id,),
            fetch_one=True
        )
        average_rating = avg_row['avg_rating'] if avg_row and avg_row['avg_rating'] else None

        # 평점 목록 (리뷰 없는 것만)
        limit_clause = f"LIMIT {limit}" if limit else ""
        rows = db.execute_query(
            f"""
            SELECT
                id,
                item_id as anime_id,
                user_id,
                rating,
                'RATED' as status,
                activity_time as updated_at,
                created_at,
                item_title as title_romaji,
                item_title as title_english,
                item_title_korean as title_korean,
                item_image as image_url,
                NULL as season_year,
                NULL as episodes
            FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating'
            AND (review_content IS NULL OR review_content = '')
            ORDER BY activity_time DESC
            {limit_clause}
            """,
            (user_id,)
        )
    else:
        # 전체 개수
        total = db.execute_query(
            """SELECT COUNT(*) as total FROM activities
               WHERE user_id = ? AND activity_type = 'anime_rating'""",
            (user_id,),
            fetch_one=True
        )['total']

        # 평균 평점
        avg_row = db.execute_query(
            """
            SELECT AVG(rating) as avg_rating
            FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating' AND rating IS NOT NULL
            """,
            (user_id,),
            fetch_one=True
        )
        average_rating = avg_row['avg_rating'] if avg_row and avg_row['avg_rating'] else None

        # 평점 목록 - activities 테이블에서 조회
        limit_clause = f"LIMIT {limit}" if limit else ""
        rows = db.execute_query(
            f"""
            SELECT
                id,
                item_id as anime_id,
                user_id,
                rating,
                'RATED' as status,
                activity_time as updated_at,
                created_at,
                item_title as title_romaji,
                item_title as title_english,
                item_title_korean as title_korean,
                item_image as image_url,
                NULL as season_year,
                NULL as episodes
            FROM activities
            WHERE user_id = ? AND activity_type = 'anime_rating'
            ORDER BY activity_time DESC
            {limit_clause}
            """,
            (user_id,)
        )

    items = [RatingResponse(**dict_from_row(row)) for row in rows]

    return UserRatingListResponse(
        items=items,
        total=total,
        average_rating=average_rating
    )


def get_all_user_ratings(user_id: int) -> Dict:
    """
    사용자의 모든 평점을 한 번에 조회 (RATED, WANT_TO_WATCH, PASS)
    3개의 API 호출을 1개로 줄여 성능 향상
    """
    # Part 1: RATED - activities 테이블에서 빠르게 조회
    rated_rows = db.execute_query(
        """
        SELECT
            id,
            item_id as anime_id,
            user_id,
            rating,
            'RATED' as status,
            activity_time as updated_at,
            created_at,
            item_title as title_romaji,
            item_title as title_english,
            item_title_korean as title_korean,
            item_image as image_url,
            NULL as season_year,
            NULL as episodes
        FROM activities
        WHERE user_id = ? AND activity_type = 'anime_rating'
        ORDER BY activity_time DESC
        """,
        (user_id,)
    )

    # Part 2: WANT_TO_WATCH - user_ratings 테이블에서 조회
    watchlist_rows = db.execute_query(
        """
        SELECT
            ur.*,
            a.title_romaji,
            a.title_english,
            a.title_korean,
            a.cover_image_url as image_url,
            a.season_year,
            a.episodes
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'WANT_TO_WATCH'
        ORDER BY ur.updated_at DESC
        """,
        (user_id,)
    )

    # Part 3: PASS - user_ratings 테이블에서 조회
    pass_rows = db.execute_query(
        """
        SELECT
            ur.*,
            a.title_romaji,
            a.title_english,
            a.title_korean,
            a.cover_image_url as image_url,
            a.season_year,
            a.episodes
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'PASS'
        ORDER BY ur.updated_at DESC
        """,
        (user_id,)
    )

    # 평균 평점 계산 (RATED만)
    avg_row = db.execute_query(
        """
        SELECT AVG(rating) as avg_rating
        FROM activities
        WHERE user_id = ? AND activity_type = 'anime_rating' AND rating IS NOT NULL
        """,
        (user_id,),
        fetch_one=True
    )
    average_rating = avg_row['avg_rating'] if avg_row and avg_row['avg_rating'] else None

    return {
        'rated': [RatingResponse(**dict_from_row(row)) for row in rated_rows],
        'watchlist': [RatingResponse(**dict_from_row(row)) for row in watchlist_rows],
        'pass': [RatingResponse(**dict_from_row(row)) for row in pass_rows],
        'total_rated': len(rated_rows),
        'total_watchlist': len(watchlist_rows),
        'total_pass': len(pass_rows),
        'average_rating': average_rating
    }


def delete_rating(user_id: int, anime_id: int) -> bool:
    """평점 삭제 (관련 댓글과 좋아요도 함께 삭제)"""

    # 먼저 관련 activity 댓글과 좋아요 삭제
    db.execute_update(
        """
        DELETE FROM activity_comments
        WHERE activity_type = 'anime_rating'
        AND activity_user_id = ?
        AND item_id = ?
        """,
        (user_id, anime_id)
    )

    db.execute_update(
        """
        DELETE FROM activity_likes
        WHERE activity_type = 'anime_rating'
        AND activity_user_id = ?
        AND item_id = ?
        """,
        (user_id, anime_id)
    )

    # 평점 삭제
    rowcount = db.execute_update(
        "DELETE FROM user_ratings WHERE user_id = ? AND anime_id = ?",
        (user_id, anime_id)
    )

    if rowcount > 0:
        # 사용자 통계 업데이트
        _update_user_stats(user_id)
        return True

    return False


def _sync_to_activities(user_id: int, anime_id: int):
    """user_ratings 데이터를 activities 테이블에 동기화 (트리거 대체)"""

    # 사용자 정보와 평점 정보 조회
    data = db.execute_query(
        """
        SELECT
            ur.user_id,
            ur.anime_id,
            ur.rating,
            ur.created_at,
            ur.updated_at,
            u.username,
            u.display_name,
            u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score,
            a.title_romaji,
            a.title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
            r.title as review_title,
            r.content as review_content,
            COALESCE(r.is_spoiler, 0) as is_spoiler
        FROM user_ratings ur
        JOIN users u ON u.id = ur.user_id
        JOIN anime a ON a.id = ur.anime_id
        LEFT JOIN user_stats us ON us.user_id = ur.user_id
        LEFT JOIN user_reviews r ON r.user_id = ur.user_id AND r.anime_id = ur.anime_id
        WHERE ur.user_id = ? AND ur.anime_id = ? AND ur.status = 'RATED'
        """,
        (user_id, anime_id),
        fetch_one=True
    )

    if data:
        # activities 테이블에 INSERT
        db.execute_update(
            """
            INSERT INTO activities (
                activity_type, user_id, item_id, activity_time,
                username, display_name, avatar_url, otaku_score,
                item_title, item_title_korean, item_image,
                rating, review_title, review_content, is_spoiler,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'anime_rating',
                data['user_id'],
                data['anime_id'],
                data['created_at'],
                data['username'],
                data['display_name'],
                data['avatar_url'],
                data['otaku_score'],
                data['title_romaji'],
                data['title_korean'],
                data['item_image'],
                data['rating'],
                data['review_title'],
                data['review_content'],
                data['is_spoiler'],
                data['created_at'],
                data['updated_at']
            )
        )


def _update_user_stats(user_id: int):
    """사용자 통계 업데이트"""

    # 평점 통계 계산
    stats = db.execute_query(
        """
        SELECT
            COUNT(CASE WHEN status = 'RATED' THEN 1 END) as total_rated,
            COUNT(CASE WHEN status = 'WANT_TO_WATCH' THEN 1 END) as total_want_to_watch,
            COUNT(CASE WHEN status = 'PASS' THEN 1 END) as total_pass,
            AVG(CASE WHEN status = 'RATED' AND rating IS NOT NULL THEN rating END) as avg_rating
        FROM user_ratings
        WHERE user_id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    # 리뷰 수
    review_count = db.execute_query(
        "SELECT COUNT(*) as total FROM user_reviews WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )['total']

    # 시청 시간 계산 (평가한 애니메이션의 에피소드 * 평균 길이)
    watch_time = db.execute_query(
        """
        SELECT SUM(a.episodes * COALESCE(a.duration, 24)) as total_minutes
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        """,
        (user_id,),
        fetch_one=True
    )['total_minutes'] or 0

    # 캐릭터 평가 수
    character_rating_count = db.execute_query(
        "SELECT COUNT(*) as total FROM character_ratings WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )['total']

    # Otaku 점수 계산
    # 공식: (애니메이션 평가수 × 2) + (캐릭터 평가수 × 1) + (리뷰수 × 5)
    otaku_score = (stats['total_rated'] * 2) + (character_rating_count * 1) + (review_count * 5)

    # 선호 장르 찾기 (가장 많이 평가한 장르)
    favorite_genre_row = db.execute_query(
        """
        SELECT g.name, COUNT(*) as cnt
        FROM user_ratings ur
        JOIN anime_genre ag ON ur.anime_id = ag.anime_id
        JOIN genre g ON ag.genre_id = g.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        GROUP BY g.name
        ORDER BY cnt DESC
        LIMIT 1
        """,
        (user_id,),
        fetch_one=True
    )
    favorite_genre = favorite_genre_row['name'] if favorite_genre_row else None

    # user_stats 업데이트
    db.execute_update(
        """
        INSERT OR REPLACE INTO user_stats (
            user_id, total_rated, total_want_to_watch, total_pass,
            average_rating, total_reviews, total_character_ratings, total_watch_time_minutes,
            otaku_score, favorite_genre, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            user_id,
            stats['total_rated'],
            stats['total_want_to_watch'],
            stats['total_pass'],
            stats['avg_rating'],
            review_count,
            character_rating_count,
            watch_time,
            otaku_score,
            favorite_genre
        )
    )
