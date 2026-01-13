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
    전체 사용자의 최근 활동 피드 (feed_activities 테이블 사용)
    - 단일 테이블 조회로 극도로 빠른 성능
    - 30개씩 로드해도 무리 없음
    """

    # feed_activities 테이블에서 직접 조회
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
            review_id,
            review_content,
            post_content,
            0 as comments_count
        FROM feed_activities
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
    특정 사용자의 활동 피드
    """

    # 애니메이션 평가 활동 (리뷰와 함께)
    anime_ratings = db.execute_query(
        """
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
            r.content as review_content,
            NULL as post_content,
            COALESCE(r.id, (SELECT id FROM user_reviews WHERE user_id = ur.user_id AND anime_id = ur.anime_id LIMIT 1)) as review_id,
            COALESCE((SELECT COUNT(*) FROM review_comments rc
             JOIN user_reviews ur2 ON rc.review_id = ur2.id
             WHERE ur2.user_id = ur.user_id AND ur2.anime_id = ur.anime_id AND rc.review_type = 'anime'), 0) as comments_count,
            CASE
                WHEN r.id IS NOT NULL THEN (SELECT COALESCE(likes_count, 0) FROM user_reviews WHERE id = r.id)
                ELSE (SELECT COUNT(*) FROM activity_likes
                      WHERE activity_type = 'anime_rating'
                      AND activity_user_id = ur.user_id
                      AND item_id = ur.anime_id)
            END as likes_count,
            CASE WHEN ? IS NOT NULL THEN
                CASE
                    WHEN r.id IS NOT NULL THEN (SELECT COUNT(*) FROM review_likes
                                                 WHERE user_id = ? AND review_id = r.id) > 0
                    ELSE (SELECT COUNT(*) FROM activity_likes
                          WHERE user_id = ?
                          AND activity_type = 'anime_rating'
                          AND activity_user_id = ur.user_id
                          AND item_id = ur.anime_id) > 0
                END
            ELSE 0 END as user_has_liked
        FROM user_ratings ur
        JOIN users u ON ur.user_id = u.id
        JOIN anime a ON ur.anime_id = a.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN user_reviews r ON ur.user_id = r.user_id AND ur.anime_id = r.anime_id
        WHERE ur.user_id = ? AND ur.status = 'RATED' AND ur.rating IS NOT NULL
        ORDER BY COALESCE(r.created_at, ur.updated_at) DESC
        """,
        (current_user_id, current_user_id, current_user_id, user_id)
    )

    # 캐릭터 평가 활동 (리뷰와 함께)
    character_ratings = db.execute_query(
        """
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
            (SELECT a.title_romaji FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END, a.start_date ASC, a.popularity DESC LIMIT 1) as anime_title,
            (SELECT a.title_korean FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END, a.start_date ASC, a.popularity DESC LIMIT 1) as anime_title_korean,
            rev.content as review_content,
            NULL as post_content,
            COALESCE(rev.id, (SELECT id FROM character_reviews WHERE user_id = cr.user_id AND character_id = cr.character_id LIMIT 1)) as review_id,
            COALESCE((SELECT COUNT(*) FROM review_comments rc
             JOIN character_reviews chr ON rc.review_id = chr.id
             WHERE chr.user_id = cr.user_id AND chr.character_id = cr.character_id AND rc.review_type = 'character'), 0) as comments_count,
            CASE
                WHEN rev.id IS NOT NULL THEN (SELECT COALESCE(likes_count, 0) FROM character_reviews WHERE id = rev.id)
                ELSE (SELECT COUNT(*) FROM activity_likes
                      WHERE activity_type = 'character_rating'
                      AND activity_user_id = cr.user_id
                      AND item_id = cr.character_id)
            END as likes_count,
            CASE WHEN ? IS NOT NULL THEN
                CASE
                    WHEN rev.id IS NOT NULL THEN (SELECT COUNT(*) FROM character_review_likes
                                                    WHERE user_id = ? AND review_id = rev.id) > 0
                    ELSE (SELECT COUNT(*) FROM activity_likes
                          WHERE user_id = ?
                          AND activity_type = 'character_rating'
                          AND activity_user_id = cr.user_id
                          AND item_id = cr.character_id) > 0
                END
            ELSE 0 END as user_has_liked
        FROM character_ratings cr
        JOIN users u ON cr.user_id = u.id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        LEFT JOIN character_reviews rev ON cr.user_id = rev.user_id AND cr.character_id = rev.character_id
        WHERE cr.user_id = ? AND cr.rating IS NOT NULL
        ORDER BY COALESCE(rev.created_at, cr.updated_at) DESC
        """,
        (current_user_id, current_user_id, current_user_id, user_id)
    )

    # 캐릭터 리뷰 활동 (평점 없이 리뷰만 작성한 경우)
    character_reviews = db.execute_query(
        """
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
            cr.id as review_id,
            cr.content as review_content,
            NULL as post_content,
            (SELECT COUNT(*) FROM review_comments
             WHERE review_id = cr.id AND review_type = 'character') as comments_count,
            (SELECT a.title_romaji FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END, a.start_date ASC, a.popularity DESC LIMIT 1) as anime_title,
            (SELECT a.title_korean FROM anime a
             JOIN anime_character ac ON a.id = ac.anime_id
             WHERE ac.character_id = c.id
             ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END, a.start_date ASC, a.popularity DESC LIMIT 1) as anime_title_korean,
            (SELECT COUNT(*) FROM activity_likes
             WHERE activity_type = 'character_review'
             AND activity_user_id = cr.user_id
             AND item_id = cr.character_id) as likes_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes
                 WHERE user_id = ?
                 AND activity_type = 'character_review'
                 AND activity_user_id = cr.user_id
                 AND item_id = cr.character_id) > 0
            ELSE 0 END as user_has_liked
        FROM character_reviews cr
        JOIN users u ON cr.user_id = u.id
        JOIN character c ON cr.character_id = c.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE cr.user_id = ?
        AND NOT EXISTS (
            SELECT 1 FROM character_ratings cr2
            WHERE cr2.user_id = cr.user_id
            AND cr2.character_id = cr.character_id
            AND cr2.rating IS NOT NULL
        )
        ORDER BY cr.created_at DESC
        """,
        (current_user_id, current_user_id, user_id)
    )

    # 리뷰만 있는 활동 (평점 없이 리뷰만 작성한 경우)
    reviews = db.execute_query(
        """
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
            r.id as review_id,
            r.content as review_content,
            NULL as post_content,
            NULL as anime_title,
            NULL as anime_title_korean,
            (SELECT COUNT(*) FROM review_comments
             WHERE review_id = r.id AND review_type = 'anime') as comments_count,
            (SELECT COUNT(*) FROM activity_likes
             WHERE activity_type = 'anime_review'
             AND activity_user_id = r.user_id
             AND item_id = r.anime_id) as likes_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes
                 WHERE user_id = ?
                 AND activity_type = 'anime_review'
                 AND activity_user_id = r.user_id
                 AND item_id = r.anime_id) > 0
            ELSE 0 END as user_has_liked
        FROM user_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN anime a ON r.anime_id = a.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE r.user_id = ?
        AND NOT EXISTS (
            SELECT 1 FROM user_ratings ur
            WHERE ur.user_id = r.user_id
            AND ur.anime_id = r.anime_id
            AND ur.status = 'RATED'
            AND ur.rating IS NOT NULL
        )
        ORDER BY r.created_at DESC
        """,
        (current_user_id, current_user_id, user_id)
    )

    # 일반 포스트 활동
    posts = db.execute_query(
        """
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
            up.content as post_content,
            NULL as review_content,
            NULL as review_id,
            NULL as anime_title,
            NULL as anime_title_korean,
            (SELECT COUNT(*) FROM activity_comments
             WHERE activity_type = 'post'
             AND activity_user_id = up.user_id
             AND item_id = up.id) as comments_count,
            (SELECT COUNT(*) FROM activity_likes
             WHERE activity_type = 'post'
             AND activity_user_id = up.user_id
             AND item_id = up.id) as likes_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes
                 WHERE user_id = ?
                 AND activity_type = 'post'
                 AND activity_user_id = up.user_id
                 AND item_id = up.id) > 0
            ELSE 0 END as user_has_liked
        FROM user_posts up
        JOIN users u ON up.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE up.user_id = ?
        ORDER BY up.created_at DESC
        """,
        (current_user_id, current_user_id, user_id)
    )

    # 모든 활동 합치고 시간순 정렬
    all_activities = []
    # 애니 평점
    anime_rating_dicts = [dict_from_row(row) for row in anime_ratings]
    all_activities.extend(anime_rating_dicts)
    # 캐릭터 평점
    character_rating_dicts = [dict_from_row(row) for row in character_ratings]
    all_activities.extend(character_rating_dicts)
    # 애니 리뷰
    review_dicts = [dict_from_row(row) for row in reviews]
    all_activities.extend(review_dicts)
    # 캐릭터 리뷰
    character_review_dicts = [dict_from_row(row) for row in character_reviews]
    all_activities.extend(character_review_dicts)
    # 사용자 게시글
    all_activities.extend([dict_from_row(row) for row in posts])

    # 시간순 정렬
    all_activities.sort(key=lambda x: x['activity_time'], reverse=True)

    # offset과 limit 적용
    return all_activities[offset:offset + limit]
