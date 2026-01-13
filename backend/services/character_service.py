"""
Character Service
캐릭터 관련 비즈니스 로직
"""
from typing import List, Dict, Optional
from database import db, dict_from_row


def get_user_rated_characters(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    사용자가 평가한 캐릭터들 조회
    """
    rows = db.execute_query(
        """
        SELECT
            c.id as character_id,
            c.name_full as character_name,
            c.name_native,
            COALESCE('/' || c.image_local, c.image_url) as character_image,
            cr.rating,
            cr.status,
            cr.updated_at,
            (SELECT a2.id FROM anime a2
             JOIN anime_character ac2 ON a2.id = ac2.anime_id
             WHERE ac2.character_id = c.id
             ORDER BY CASE WHEN ac2.role = 'MAIN' THEN 0 ELSE 1 END, a2.start_date ASC, a2.popularity DESC
             LIMIT 1) as anime_id,
            (SELECT COALESCE(a2.title_korean, a2.title_romaji) FROM anime a2
             JOIN anime_character ac2 ON a2.id = ac2.anime_id
             WHERE ac2.character_id = c.id
             ORDER BY CASE WHEN ac2.role = 'MAIN' THEN 0 ELSE 1 END, a2.start_date ASC, a2.popularity DESC
             LIMIT 1) as anime_title,
            (SELECT COALESCE('/' || a2.cover_image_local, a2.cover_image_url) FROM anime a2
             JOIN anime_character ac2 ON a2.id = ac2.anime_id
             WHERE ac2.character_id = c.id
             ORDER BY CASE WHEN ac2.role = 'MAIN' THEN 0 ELSE 1 END, a2.start_date ASC, a2.popularity DESC
             LIMIT 1) as image_url
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ? AND cr.rating IS NOT NULL
        ORDER BY cr.updated_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    return [dict_from_row(row) for row in rows]


def get_characters_from_rated_anime(user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    사용자가 평가한 애니메이션의 캐릭터들 조회 (평가하지 않은 캐릭터만)
    같은 캐릭터가 여러 애니메이션에 나오면 가장 인기있는 애니메이션 하나만 표시
    """
    # 먼저 캐릭터 기본 정보와 최우선 애니메이션 ID를 가져옴
    rows = db.execute_query(
        """
        WITH RankedCharacters AS (
            SELECT
                c.id,
                c.name_full,
                c.name_native,
                COALESCE('/' || c.image_local, c.image_url) as image_url,
                c.gender,
                c.favourites,
                MIN(CASE ac.role WHEN 'MAIN' THEN 1 WHEN 'SUPPORTING' THEN 2 ELSE 3 END) as role_priority,
                cr.rating as my_rating,
                cr.status as my_status,
                cr.created_at as rated_at
            FROM user_ratings ur
            JOIN anime a ON ur.anime_id = a.id
            JOIN anime_character ac ON a.id = ac.anime_id
            JOIN character c ON ac.character_id = c.id
            LEFT JOIN character_ratings cr ON c.id = cr.character_id AND cr.user_id = ?
            WHERE ur.user_id = ?
                AND ur.status = 'RATED'
                AND ac.role IN ('MAIN', 'SUPPORTING')
                AND cr.rating IS NULL
                AND c.name_full NOT IN ('Narrator', 'Unknown', 'Extra', 'Background Character', 'Announcer', 'Bystander', 'Crowd', 'Student', 'Villager', 'Child', 'Teacher', 'Soldier', 'Guard', 'Clerk', 'Reporter', 'Doctor', 'Nurse', 'Customer', 'Passerby')
                AND c.name_full NOT LIKE 'Narrator%'
                AND c.name_full NOT LIKE 'Unknown%'
                AND c.name_full NOT LIKE 'Extra%'
                AND c.name_full NOT LIKE 'Background%'
                AND c.name_full NOT LIKE 'Student %'
                AND c.name_full NOT LIKE 'Villager %'
                AND c.name_full NOT LIKE 'Soldier %'
                AND c.name_full NOT LIKE 'Customer %'
                AND c.name_full NOT LIKE 'Guard %'
            GROUP BY c.id
        ),
        CharacterAnime AS (
            SELECT
                rc.id as character_id,
                a2.id as anime_id,
                a2.title_romaji,
                a2.title_korean,
                COALESCE('/' || a2.cover_image_local, a2.cover_image_url) as anime_cover,
                ac3.role,
                ROW_NUMBER() OVER (
                    PARTITION BY rc.id
                    ORDER BY
                        CASE WHEN NOT EXISTS (SELECT 1 FROM anime_relation ar WHERE ar.anime_id = a2.id AND ar.relation_type = 'PREQUEL') THEN 0 ELSE 1 END,
                        a2.popularity DESC
                ) as rn
            FROM RankedCharacters rc
            JOIN anime_character ac3 ON ac3.character_id = rc.id
            JOIN anime a2 ON ac3.anime_id = a2.id
            JOIN user_ratings ur2 ON ur2.anime_id = a2.id AND ur2.user_id = ? AND ur2.status = 'RATED'
        )
        SELECT
            rc.*,
            ca.anime_id,
            ca.title_romaji as anime_title,
            ca.title_korean as anime_title_korean,
            ca.anime_cover,
            ca.role
        FROM RankedCharacters rc
        LEFT JOIN CharacterAnime ca ON ca.character_id = rc.id AND ca.rn = 1
        ORDER BY rc.favourites DESC, rc.role_priority ASC
        LIMIT ? OFFSET ?
        """,
        (user_id, user_id, user_id, limit, offset)
    )

    return [dict_from_row(row) for row in rows]


def get_character_rating(user_id: int, character_id: int) -> Optional[Dict]:
    """
    특정 캐릭터에 대한 사용자 평가 조회
    """
    row = db.execute_query(
        """
        SELECT
            id,
            user_id,
            character_id,
            rating,
            status,
            created_at,
            updated_at
        FROM character_ratings
        WHERE user_id = ? AND character_id = ?
        """,
        (user_id, character_id),
        fetch_one=True
    )

    return dict_from_row(row) if row else None


def create_or_update_character_rating(user_id: int, character_id: int, rating: float = None, status: str = None) -> Dict:
    """
    캐릭터 평가 생성 또는 수정
    """
    # Check if rating exists
    existing = get_character_rating(user_id, character_id)

    if existing:
        # Update - only update fields that are provided
        update_parts = []
        params = []

        if rating is not None:
            update_parts.append("rating = ?")
            params.append(rating)

        if status is not None:
            update_parts.append("status = ?")
            params.append(status)

        if update_parts:
            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([user_id, character_id])

            db.execute_update(
                f"""
                UPDATE character_ratings
                SET {', '.join(update_parts)}
                WHERE user_id = ? AND character_id = ?
                """,
                tuple(params)
            )
    else:
        # Insert
        if rating is None and status is None:
            return None

        db.execute_insert(
            """
            INSERT INTO character_ratings (user_id, character_id, rating, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, character_id, rating, status or 'RATED')
        )

    # Update user stats (otaku score)
    from services.rating_service import _update_user_stats
    _update_user_stats(user_id)

    return get_character_rating(user_id, character_id)


def delete_character_rating(user_id: int, character_id: int) -> bool:
    """
    캐릭터 평가 삭제 (관련 댓글과 좋아요도 함께 삭제)
    """
    # 먼저 관련 activity 댓글과 좋아요 삭제
    db.execute_update(
        """
        DELETE FROM activity_comments
        WHERE activity_type = 'character_rating'
        AND activity_user_id = ?
        AND item_id = ?
        """,
        (user_id, character_id)
    )

    db.execute_update(
        """
        DELETE FROM activity_likes
        WHERE activity_type = 'character_rating'
        AND activity_user_id = ?
        AND item_id = ?
        """,
        (user_id, character_id)
    )

    # 평점 삭제
    db.execute_update(
        """
        DELETE FROM character_ratings
        WHERE user_id = ? AND character_id = ?
        """,
        (user_id, character_id)
    )

    # Update user stats (otaku score)
    from services.rating_service import _update_user_stats
    _update_user_stats(user_id)

    return True


def get_user_character_stats(user_id: int) -> Dict:
    """
    사용자의 캐릭터 평가 통계
    """
    row = db.execute_query(
        """
        SELECT
            COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as total_rated,
            AVG(CASE WHEN rating IS NOT NULL THEN rating END) as average_rating,
            COUNT(CASE WHEN rating >= 4.5 THEN 1 END) as five_star_count,
            COUNT(CASE WHEN rating >= 4.0 AND rating < 4.5 THEN 1 END) as four_star_count,
            COUNT(CASE WHEN status = 'WANT_TO_KNOW' THEN 1 END) as total_want_to_know,
            COUNT(CASE WHEN status = 'NOT_INTERESTED' THEN 1 END) as total_not_interested
        FROM character_ratings
        WHERE user_id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    return dict_from_row(row) if row else {
        'total_rated': 0,
        'average_rating': None,
        'five_star_count': 0,
        'four_star_count': 0,
        'total_want_to_know': 0,
        'total_not_interested': 0
    }


def get_character_detail(character_id: int, user_id: int) -> Optional[Dict]:
    """
    캐릭터 상세 정보 조회
    """
    # Get character basic info
    char_row = db.execute_query(
        """
        SELECT
            c.id,
            c.name_full,
            c.name_native,
            COALESCE('/' || c.image_local, c.image_url) as image_url,
            c.gender,
            c.date_of_birth,
            c.age,
            c.blood_type,
            c.description,
            c.favourites,
            cr.rating as my_rating,
            cr.status as my_status,
            cr.created_at as rating_created_at
        FROM character c
        LEFT JOIN character_ratings cr ON c.id = cr.character_id AND cr.user_id = ?
        WHERE c.id = ?
        """,
        (user_id, character_id),
        fetch_one=True
    )

    if not char_row:
        return None

    character = dict_from_row(char_row)

    # Get anime appearances
    anime_rows = db.execute_query(
        """
        SELECT
            a.id as anime_id,
            a.title_romaji,
            a.title_english,
            a.title_korean,
            COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image,
            ac.role,
            ur.rating as my_anime_rating
        FROM anime_character ac
        JOIN anime a ON ac.anime_id = a.id
        LEFT JOIN user_ratings ur ON a.id = ur.anime_id AND ur.user_id = ? AND ur.status = 'RATED'
        WHERE ac.character_id = ?
        ORDER BY
            CASE ac.role
                WHEN 'MAIN' THEN 1
                WHEN 'SUPPORTING' THEN 2
                ELSE 3
            END,
            a.popularity DESC
        """,
        (user_id, character_id)
    )

    character['anime'] = [dict_from_row(row) for row in anime_rows]

    # Get site rating statistics
    site_stats_row = db.execute_query(
        """
        SELECT
            COUNT(*) as rating_count,
            AVG(rating) as average_rating
        FROM character_ratings
        WHERE character_id = ? AND rating IS NOT NULL
        """,
        (character_id,),
        fetch_one=True
    )
    character['site_rating_count'] = site_stats_row['rating_count'] if site_stats_row else 0
    character['site_average_rating'] = site_stats_row['average_rating'] if site_stats_row else None

    # Get site rating distribution
    rating_dist_rows = db.execute_query(
        """
        SELECT
            rating,
            COUNT(*) as count
        FROM character_ratings
        WHERE character_id = ? AND rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating DESC
        """,
        (character_id,)
    )
    character['site_rating_distribution'] = [dict_from_row(row) for row in rating_dist_rows]

    return character
