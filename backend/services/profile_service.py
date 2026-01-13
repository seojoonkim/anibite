"""
Profile Service
사용자 프로필, 통계 조회
"""
from typing import Optional, Dict, List
from database import db, dict_from_row
from models.user import UserStatsResponse, UserProfileResponse, UserPublicResponse


def get_user_stats(user_id: int) -> Optional[UserStatsResponse]:
    """사용자 통계 조회"""

    row = db.execute_query(
        """
        SELECT * FROM user_stats WHERE user_id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    if row is None:
        return None

    return UserStatsResponse(**dict_from_row(row))


def get_user_profile(user_id: int) -> Optional[UserProfileResponse]:
    """사용자 프로필 (정보 + 통계)"""

    # 사용자 정보
    user_row = db.execute_query(
        """
        SELECT id, username, display_name, avatar_url, bio, created_at
        FROM users WHERE id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    if user_row is None:
        return None

    user = UserPublicResponse(**dict_from_row(user_row))

    # 통계
    stats = get_user_stats(user_id)

    return UserProfileResponse(user=user, stats=stats)


def get_genre_preferences(user_id: int, limit: int = 10) -> List[Dict]:
    """장르별 선호도 (평균 평점)"""

    rows = db.execute_query(
        """
        SELECT
            g.name as genre,
            COUNT(*) as count,
            AVG(ur.rating) as avg_rating,
            MAX(ur.rating) as max_rating,
            MIN(ur.rating) as min_rating,
            (COUNT(*) * AVG(ur.rating)) as score
        FROM user_ratings ur
        JOIN anime_genre ag ON ur.anime_id = ag.anime_id
        JOIN genre g ON ag.genre_id = g.id
        WHERE ur.user_id = ? AND ur.status = 'RATED' AND ur.rating IS NOT NULL
        GROUP BY g.name
        HAVING count >= 2
        ORDER BY score DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_rating_distribution(user_id: int) -> List[Dict]:
    """평점 분포"""

    rows = db.execute_query(
        """
        SELECT
            rating,
            COUNT(*) as count
        FROM user_ratings
        WHERE user_id = ? AND status = 'RATED' AND rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_watch_history(user_id: int, limit: int = 50) -> List[Dict]:
    """최근 평가한 애니메이션"""

    rows = db.execute_query(
        """
        SELECT
            a.id,
            a.title_romaji,
            a.title_english,
            a.cover_image_url,
            ur.rating,
            ur.status,
            ur.updated_at
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
        ORDER BY ur.updated_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_watch_time(user_id: int) -> Dict:
    """시청 시간 계산 (평가한 애니메이션의 총 재생시간)"""

    row = db.execute_query(
        """
        SELECT
            SUM(a.episodes * COALESCE(a.duration, 24)) as total_minutes
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        """,
        (user_id,),
        fetch_one=True
    )

    total_minutes = row['total_minutes'] if row and row['total_minutes'] else 0

    return {
        'total_minutes': int(total_minutes),
        'total_hours': round(total_minutes / 60, 1),
        'total_days': round(total_minutes / 1440, 1)
    }


def get_year_distribution(user_id: int) -> List[Dict]:
    """연도별 시청 분포 (사용자가 본 애니메이션들의 방영 연도)"""

    rows = db.execute_query(
        """
        SELECT
            a.season_year as year,
            COUNT(*) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND a.season_year IS NOT NULL
            AND a.season_year >= 1960
            AND a.season_year <= 2026
        GROUP BY a.season_year
        ORDER BY a.season_year ASC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_format_distribution(user_id: int) -> List[Dict]:
    """포맷별 분포 (TV, MOVIE, OVA, ONA 등)"""

    rows = db.execute_query(
        """
        SELECT
            a.format,
            COUNT(*) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND a.format IS NOT NULL
        GROUP BY a.format
        ORDER BY count DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_episode_length_distribution(user_id: int) -> List[Dict]:
    """에피소드 길이별 분포 (단편/중편/장편)"""

    rows = db.execute_query(
        """
        SELECT
            CASE
                WHEN a.episodes <= 12 THEN 'SHORT'
                WHEN a.episodes <= 26 THEN 'MEDIUM'
                ELSE 'LONG'
            END as length_category,
            COUNT(*) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND a.episodes IS NOT NULL
            AND a.episodes > 0
        GROUP BY length_category
        ORDER BY count DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_rating_stats(user_id: int) -> Dict:
    """평점 통계 (표준편차, 최빈값 등)"""

    row = db.execute_query(
        """
        SELECT
            COUNT(*) as total_ratings,
            AVG(rating) as mean_rating,
            MIN(rating) as min_rating,
            MAX(rating) as max_rating
        FROM user_ratings
        WHERE user_id = ? AND status = 'RATED' AND rating IS NOT NULL
        """,
        (user_id,),
        fetch_one=True
    )

    if not row or row['total_ratings'] == 0:
        return {
            'total_ratings': 0,
            'mean_rating': 0,
            'std_dev': 0,
            'min_rating': 0,
            'max_rating': 0
        }

    # 표준편차 계산
    ratings = db.execute_query(
        """
        SELECT rating FROM user_ratings
        WHERE user_id = ? AND status = 'RATED' AND rating IS NOT NULL
        """,
        (user_id,)
    )

    ratings_list = [r['rating'] for r in ratings]
    mean = row['mean_rating']
    variance = sum((r - mean) ** 2 for r in ratings_list) / len(ratings_list)
    std_dev = variance ** 0.5

    return {
        'total_ratings': row['total_ratings'],
        'mean_rating': round(mean, 2),
        'std_dev': round(std_dev, 2),
        'min_rating': row['min_rating'],
        'max_rating': row['max_rating']
    }


def get_studio_stats(user_id: int, limit: int = 10) -> List[Dict]:
    """스튜디오별 통계"""

    rows = db.execute_query(
        """
        SELECT
            s.name as studio_name,
            COUNT(DISTINCT a.id) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        JOIN anime_studio ast ON a.id = ast.anime_id
        JOIN studio s ON ast.studio_id = s.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
        GROUP BY s.id, s.name
        HAVING count >= 2
        ORDER BY count DESC, average_rating DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_season_stats(user_id: int) -> List[Dict]:
    """시즌별 통계 (봄/여름/가을/겨울)"""

    rows = db.execute_query(
        """
        SELECT
            a.season,
            COUNT(*) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND a.season IS NOT NULL
        GROUP BY a.season
        ORDER BY count DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_genre_combination_stats(user_id: int, limit: int = 10) -> List[Dict]:
    """장르 조합 분석 (2개 장르 조합)"""

    rows = db.execute_query(
        """
        SELECT
            g1.name as genre1,
            g2.name as genre2,
            COUNT(DISTINCT a.id) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        JOIN anime_genre ag1 ON a.id = ag1.anime_id
        JOIN genre g1 ON ag1.genre_id = g1.id
        JOIN anime_genre ag2 ON a.id = ag2.anime_id
        JOIN genre g2 ON ag2.genre_id = g2.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND g1.id < g2.id
        GROUP BY g1.name, g2.name
        HAVING count >= 2
        ORDER BY count DESC, average_rating DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_five_star_characters(user_id: int) -> List[Dict]:
    """5점 평가한 캐릭터 목록 (프로필 사진 선택용)"""

    rows = db.execute_query(
        """
        SELECT
            c.id as character_id,
            c.name_full,
            c.name_native,
            c.image_url as image_url,
            c.image_local,
            cr.rating
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
            AND cr.rating = 5.0
        ORDER BY cr.updated_at DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in rows]


def get_character_ratings(user_id: int, limit: int = 500) -> List[Dict]:
    """사용자가 평가한 캐릭터 목록 (최적화 버전 - LEFT JOIN 사용)"""

    rows = db.execute_query(
        """
        SELECT
            cr.character_id,
            c.name_full as character_name,
            c.name_native as character_name_native,
            c.image_url as image_url,
            cr.rating,
            cr.status,
            cr.updated_at,
            a.id as anime_id,
            a.title_romaji as anime_title,
            a.title_korean as anime_title_korean
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN (
            SELECT DISTINCT ac.character_id, a.id, a.title_romaji, a.title_korean,
                   ROW_NUMBER() OVER (PARTITION BY ac.character_id
                                      ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END,
                                               a.start_date ASC, a.popularity DESC) as rn
            FROM anime_character ac
            JOIN anime a ON ac.anime_id = a.id
        ) a ON c.id = a.character_id AND a.rn = 1
        WHERE cr.user_id = ?
        ORDER BY cr.updated_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_leaderboard(limit: int = 50) -> List[Dict]:
    """오타쿠 점수 리더보드 (상위 사용자)"""

    rows = db.execute_query(
        """
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.avatar_url,
            s.otaku_score,
            s.total_rated,
            s.total_character_ratings,
            s.total_reviews
        FROM users u
        INNER JOIN user_stats s ON u.id = s.user_id
        ORDER BY s.otaku_score DESC
        LIMIT ?
        """,
        (limit,)
    )

    return [dict_from_row(row) for row in rows]


def get_studio_preferences(user_id: int, limit: int = 10) -> Dict:
    """
    제작사 선호도 상세 분석
    - 좋아하는 제작사 Top N (평균 평점 4.0 이상)
    - 각 제작사별 작품 수, 평균 평점
    """

    rows = db.execute_query(
        """
        SELECT
            s.id as studio_id,
            s.name as studio_name,
            COUNT(DISTINCT a.id) as anime_count,
            AVG(ur.rating) as average_rating,
            MAX(ur.rating) as max_rating,
            MIN(ur.rating) as min_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        JOIN anime_studio ast ON a.id = ast.anime_id
        JOIN studio s ON ast.studio_id = s.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND ast.is_main = 1
        GROUP BY s.id, s.name
        HAVING anime_count >= 2
        ORDER BY average_rating DESC, anime_count DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    favorite_studios = [dict_from_row(row) for row in rows]

    # 전체 평균과 비교
    overall_avg = db.execute_query(
        """
        SELECT AVG(rating) as overall_average
        FROM user_ratings
        WHERE user_id = ? AND status = 'RATED' AND rating IS NOT NULL
        """,
        (user_id,)
    )

    return {
        'favorite_studios': favorite_studios,
        'overall_average': dict_from_row(overall_avg[0])['overall_average'] if overall_avg else 0
    }


def get_hidden_gems(user_id: int, limit: int = 10) -> List[Dict]:
    """
    숨겨진 보석 발견
    - 대중 평점은 낮지만 (< 70) 내가 높게 평가한 작품 (>= 4.0)
    - 반대로 과대평가라고 생각하는 작품도 포함
    """

    rows = db.execute_query(
        """
        SELECT
            a.id as anime_id,
            COALESCE(a.title_korean, a.title_romaji) as title,
            a.cover_image_url,
            a.cover_image_local,
            ur.rating as my_rating,
            a.average_score as anilist_score,
            (ur.rating * 20 - a.average_score) as rating_difference,
            a.popularity,
            'hidden_gem' as type
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND a.average_score IS NOT NULL
            AND ur.rating >= 4.0
            AND a.average_score < 70
        ORDER BY rating_difference DESC
        LIMIT ?
        """,
        (user_id, limit // 2)
    )

    hidden_gems = [dict_from_row(row) for row in rows]

    # 과대평가 작품
    overrated_rows = db.execute_query(
        """
        SELECT
            a.id as anime_id,
            COALESCE(a.title_korean, a.title_romaji) as title,
            a.cover_image_url,
            a.cover_image_local,
            ur.rating as my_rating,
            a.average_score as anilist_score,
            (ur.rating * 20 - a.average_score) as rating_difference,
            a.popularity,
            'overrated' as type
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND a.average_score IS NOT NULL
            AND ur.rating <= 2.5
            AND a.average_score >= 75
        ORDER BY rating_difference ASC
        LIMIT ?
        """,
        (user_id, limit // 2)
    )

    overrated = [dict_from_row(row) for row in overrated_rows]

    return hidden_gems + overrated


def get_source_preferences(user_id: int) -> Dict:
    """
    원작 매체별 선호도 분석
    - MANGA, LIGHT_NOVEL, ORIGINAL, GAME, VISUAL_NOVEL 등
    """

    rows = db.execute_query(
        """
        SELECT
            a.source,
            COUNT(*) as count,
            AVG(ur.rating) as average_rating,
            MAX(ur.rating) as max_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND a.source IS NOT NULL
        GROUP BY a.source
        ORDER BY count DESC
        """,
        (user_id,)
    )

    sources = [dict_from_row(row) for row in rows]

    # 원작별 한글 이름 매핑
    source_names = {
        'MANGA': '만화',
        'LIGHT_NOVEL': '라이트 노벨',
        'ORIGINAL': '오리지널',
        'GAME': '게임',
        'VISUAL_NOVEL': '비주얼 노벨',
        'NOVEL': '소설',
        'WEB_MANGA': '웹 만화',
        'OTHER': '기타'
    }

    for source in sources:
        source['source_korean'] = source_names.get(source['source'], source['source'])

    return {
        'sources': sources,
        'total_count': sum(s['count'] for s in sources)
    }


def get_director_preferences(user_id: int, limit: int = 10) -> List[Dict]:
    """
    감독 선호도 분석
    """

    rows = db.execute_query(
        """
        SELECT
            s.id as staff_id,
            s.name_full as director_name,
            COUNT(DISTINCT a.id) as anime_count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        JOIN anime_staff ast ON a.id = ast.anime_id
        JOIN staff s ON ast.staff_id = s.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
            AND ast.role LIKE '%Director%'
        GROUP BY s.id, s.name_full
        HAVING anime_count >= 2
        ORDER BY average_rating DESC, anime_count DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    return [dict_from_row(row) for row in rows]


def get_genre_radar_data(user_id: int) -> Dict:
    """
    레이더 차트용 장르 데이터
    - 주요 장르들의 평균 평점과 개수
    """

    rows = db.execute_query(
        """
        SELECT
            g.name as genre,
            COUNT(DISTINCT a.id) as count,
            AVG(ur.rating) as average_rating
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        JOIN anime_genre ag ON a.id = ag.anime_id
        JOIN genre g ON ag.genre_id = g.id
        WHERE ur.user_id = ?
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
        GROUP BY g.id, g.name
        ORDER BY count DESC
        """,
        (user_id,)
    )

    genres = [dict_from_row(row) for row in rows]

    # 상위 8개 장르만 선택 (레이더 차트에 적합)
    top_genres = genres[:8] if len(genres) >= 8 else genres

    return {
        'genres': top_genres,
        'chart_data': {
            'labels': [g['genre'] for g in top_genres],
            'ratings': [float(g['average_rating']) for g in top_genres],
            'counts': [g['count'] for g in top_genres]
        }
    }
