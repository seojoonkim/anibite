"""
Feed Service
사용자 활동 피드 - 최적화 버전
"""
from typing import List, Dict
from database import db, dict_from_row


def get_following_feed(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    팔로잉하는 사용자들의 활동 피드 (UNION ALL로 최적화)
    """
    # 팔로잉 사용자 ID 목록 조회
    following_ids = db.execute_query(
        """
        SELECT following_id FROM user_follows WHERE follower_id = ?
        """,
        (user_id,)
    )

    if not following_ids:
        return []

    following_id_list = [str(row[0]) for row in following_ids]
    placeholders = ','.join(['?' for _ in following_id_list])

    # UNION ALL로 모든 활동을 단일 쿼리로 통합
    rows = db.execute_query(
        f"""
        SELECT * FROM (
            -- 애니메이션 평가 활동
            SELECT
                'anime_rating' as activity_type,
                ur.user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score,
                ur.anime_id as item_id,
                a.title_romaji as item_title,
                a.title_korean as item_title_korean,
                COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
                ur.rating,
                ur.status,
                COALESCE(r.created_at, ur.updated_at) as activity_time,
                NULL as anime_title,
                NULL as anime_title_korean,
                NULL as anime_id,
                r.id as review_id,
                r.content as review_content,
                NULL as post_content,
                0 as comments_count
            FROM user_ratings ur
            JOIN users u ON ur.user_id = u.id
            JOIN anime a ON ur.anime_id = a.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            LEFT JOIN user_reviews r ON ur.user_id = r.user_id AND ur.anime_id = r.anime_id
            WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
                AND ur.user_id IN ({placeholders})

            UNION ALL

            -- 캐릭터 평가 활동 (LEFT JOIN으로 최적화)
            SELECT
                'character_rating' as activity_type,
                cr.user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score,
                cr.character_id as item_id,
                c.name_full as item_title,
                c.name_native as item_title_korean,
                COALESCE('/' || c.image_local, c.image_url) as item_image,
                cr.rating,
                NULL as status,
                COALESCE(rev.created_at, cr.updated_at) as activity_time,
                a.title_romaji as anime_title,
                a.title_korean as anime_title_korean,
                a.id as anime_id,
                rev.id as review_id,
                rev.content as review_content,
                NULL as post_content,
                0 as comments_count
            FROM character_ratings cr
            JOIN users u ON cr.user_id = u.id
            JOIN character c ON cr.character_id = c.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            LEFT JOIN character_reviews rev ON cr.user_id = rev.user_id AND cr.character_id = rev.character_id
            LEFT JOIN (
                SELECT DISTINCT ac.character_id, a.id, a.title_romaji, a.title_korean,
                       ROW_NUMBER() OVER (PARTITION BY ac.character_id ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END) as rn
                FROM anime_character ac
                JOIN anime a ON ac.anime_id = a.id
            ) a ON c.id = a.character_id AND a.rn = 1
            WHERE cr.rating IS NOT NULL
                AND cr.user_id IN ({placeholders})

            UNION ALL

            -- 캐릭터 리뷰 (평점 없이)
            SELECT
                'character_review' as activity_type,
                cr.user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score,
                cr.character_id as item_id,
                c.name_full as item_title,
                c.name_native as item_title_korean,
                COALESCE('/' || c.image_local, c.image_url) as item_image,
                NULL as rating,
                NULL as status,
                cr.created_at as activity_time,
                a.title_romaji as anime_title,
                a.title_korean as anime_title_korean,
                NULL as anime_id,
                cr.id as review_id,
                cr.content as review_content,
                NULL as post_content,
                0 as comments_count
            FROM character_reviews cr
            JOIN users u ON cr.user_id = u.id
            JOIN character c ON cr.character_id = c.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            LEFT JOIN (
                SELECT DISTINCT ac.character_id, a.id, a.title_romaji, a.title_korean,
                       ROW_NUMBER() OVER (PARTITION BY ac.character_id ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END) as rn
                FROM anime_character ac
                JOIN anime a ON ac.anime_id = a.id
            ) a ON c.id = a.character_id AND a.rn = 1
            WHERE cr.user_id IN ({placeholders})
            AND NOT EXISTS (
                SELECT 1 FROM character_ratings cr2
                WHERE cr2.user_id = cr.user_id
                AND cr2.character_id = cr.character_id
                AND cr2.rating IS NOT NULL
            )

            UNION ALL

            -- 애니 리뷰 (평점 없이)
            SELECT
                'anime_review' as activity_type,
                r.user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score,
                r.anime_id as item_id,
                a.title_romaji as item_title,
                a.title_korean as item_title_korean,
                COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
                NULL as rating,
                NULL as status,
                r.created_at as activity_time,
                NULL as anime_title,
                NULL as anime_title_korean,
                NULL as anime_id,
                r.id as review_id,
                r.content as review_content,
                NULL as post_content,
                0 as comments_count
            FROM user_reviews r
            JOIN users u ON r.user_id = u.id
            JOIN anime a ON r.anime_id = a.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE r.user_id IN ({placeholders})
            AND NOT EXISTS (
                SELECT 1 FROM user_ratings ur
                WHERE ur.user_id = r.user_id
                AND ur.anime_id = r.anime_id
                AND ur.status = 'RATED'
                AND ur.rating IS NOT NULL
            )

            UNION ALL

            -- 사용자 게시글
            SELECT
                'user_post' as activity_type,
                up.user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score,
                up.id as item_id,
                NULL as item_title,
                NULL as item_title_korean,
                NULL as item_image,
                NULL as rating,
                NULL as status,
                up.created_at as activity_time,
                NULL as anime_title,
                NULL as anime_title_korean,
                NULL as anime_id,
                NULL as review_id,
                NULL as review_content,
                up.content as post_content,
                0 as comments_count
            FROM user_posts up
            JOIN users u ON up.user_id = u.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE up.user_id IN ({placeholders})
        )
        ORDER BY activity_time DESC
        LIMIT ? OFFSET ?
        """,
        (*following_id_list, *following_id_list, *following_id_list, *following_id_list, *following_id_list, limit, offset)
    )

    results = [dict_from_row(row) for row in rows]

    # Batch load comments_count for performance
    _enrich_comments_count(results)

    return results


def get_global_feed(limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    전체 사용자의 최근 활동 피드 (activities 테이블 사용)
    - 단일 테이블 조회로 극도로 빠른 성능
    - 30개씩 로드해도 무리 없음
    """

    # activities 테이블에서 직접 조회
    # Note: activities 테이블에는 review_id, post_content 컬럼이 없음
    rows = db.execute_query(
        """
        SELECT
            activity_type,
            user_id,
            username,
            display_name,
            avatar_url,
            otaku_score,
            item_id,
            item_title,
            item_title_korean,
            item_image,
            rating,
            NULL as status,
            activity_time,
            anime_title,
            anime_title_korean,
            anime_id,
            NULL as review_id,
            review_content,
            NULL as post_content,
            0 as comments_count
        FROM activities
        ORDER BY activity_time DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )

    results = [dict_from_row(row) for row in rows]

    # Batch load comments_count for performance
    _enrich_comments_count(results)

    return results


def _enrich_comments_count(activities: List[Dict]):
    """
    Batch로 comments_count 조회 (성능 최적화)
    """
    if not activities:
        return

    # Group by review type
    anime_review_ids = []
    character_review_ids = []
    post_keys = []

    for activity in activities:
        if activity['review_id']:
            if activity['activity_type'] in ['anime_rating', 'anime_review']:
                anime_review_ids.append(activity['review_id'])
            elif activity['activity_type'] in ['character_rating', 'character_review']:
                character_review_ids.append(activity['review_id'])
        elif activity['activity_type'] == 'user_post':
            post_keys.append((activity['user_id'], activity['item_id']))

    # Batch query for anime review comments
    anime_comments_count = {}
    if anime_review_ids:
        placeholders = ','.join(['?' for _ in anime_review_ids])
        rows = db.execute_query(
            f"SELECT review_id, COUNT(*) as count FROM review_comments WHERE review_type = 'anime' AND review_id IN ({placeholders}) GROUP BY review_id",
            tuple(anime_review_ids)
        )
        anime_comments_count = {row[0]: row[1] for row in rows}

    # Batch query for character review comments
    character_comments_count = {}
    if character_review_ids:
        placeholders = ','.join(['?' for _ in character_review_ids])
        rows = db.execute_query(
            f"SELECT review_id, COUNT(*) as count FROM review_comments WHERE review_type = 'character' AND review_id IN ({placeholders}) GROUP BY review_id",
            tuple(character_review_ids)
        )
        character_comments_count = {row[0]: row[1] for row in rows}

    # Batch query for post comments
    post_comments_count = {}
    if post_keys:
        conditions = ' OR '.join([f"(activity_user_id = ? AND item_id = ?)" for _ in post_keys])
        params = []
        for user_id, item_id in post_keys:
            params.extend([user_id, item_id])

        rows = db.execute_query(
            f"SELECT activity_user_id, item_id, COUNT(*) as count FROM activity_comments WHERE activity_type = 'post' AND ({conditions}) GROUP BY activity_user_id, item_id",
            tuple(params)
        )
        post_comments_count = {(row[0], row[1]): row[2] for row in rows}

    # Update activities with comments_count
    for activity in activities:
        if activity['review_id']:
            if activity['activity_type'] in ['anime_rating', 'anime_review']:
                activity['comments_count'] = anime_comments_count.get(activity['review_id'], 0)
            elif activity['activity_type'] in ['character_rating', 'character_review']:
                activity['comments_count'] = character_comments_count.get(activity['review_id'], 0)
        elif activity['activity_type'] == 'user_post':
            activity['comments_count'] = post_comments_count.get((activity['user_id'], activity['item_id']), 0)


def get_user_feed(user_id: int, current_user_id: int = None, limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    특정 사용자의 활동 피드 (activities 테이블 사용)
    - 단일 테이블 조회로 극도로 빠른 성능
    """

    # activities 테이블에서 user_id로 필터링
    # Note: activities 테이블에는 review_id, post_content 컬럼이 없음
    rows = db.execute_query(
        """
        SELECT
            activity_type,
            user_id,
            username,
            display_name,
            avatar_url,
            otaku_score,
            item_id,
            item_title,
            item_title_korean,
            item_image,
            rating,
            NULL as status,
            activity_time,
            anime_title,
            anime_title_korean,
            anime_id,
            NULL as review_id,
            review_content,
            NULL as post_content,
            0 as comments_count
        FROM activities
        WHERE user_id = ?
        ORDER BY activity_time DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    results = [dict_from_row(row) for row in rows]

    # Batch load comments_count for performance
    _enrich_comments_count(results)

    return results
