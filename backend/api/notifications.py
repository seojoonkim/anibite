"""
Notifications API - 사용자 알림 관리
내가 작성한 피드에 좋아요나 댓글을 받은 것을 알림으로 보여줌
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from api.deps import get_current_user
from database import get_db, Database
from models.user import UserResponse

router = APIRouter()


@router.get("/")
async def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    사용자의 알림 목록을 반환
    - 내가 작성한 활동(평가/리뷰)에 다른 사용자가 좋아요나 댓글을 남긴 경우
    """
    notifications = []

    try:
        print(f"[Notifications API] Loading notifications for user {current_user.id} ({current_user.username})")

        # 1. 좋아요 알림 가져오기 (anime_rating + character_rating)
        like_query = """
        SELECT
            'like' as notification_type,
            al.created_at as notification_time,
            al.activity_type,
            al.activity_user_id,
            al.item_id,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN COALESCE(a.title_korean, a.title_romaji, a.title_english)
                WHEN al.activity_type = 'character_rating' THEN c.name_full
            END as item_title,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN a.cover_image_url
                WHEN al.activity_type = 'character_rating' THEN c.image_url
            END as item_image,
            CASE
                WHEN al.activity_type = 'character_rating' THEN char_anime.id
                ELSE NULL
            END as anime_id,
            CASE
                WHEN al.activity_type = 'character_rating' THEN char_anime.title_romaji
                ELSE NULL
            END as anime_title,
            CASE
                WHEN al.activity_type = 'character_rating' THEN char_anime.title_korean
                ELSE NULL
            END as anime_title_korean,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN ur.rating
                WHEN al.activity_type = 'character_rating' THEN cr.rating
            END as my_rating,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN urv.content
                WHEN al.activity_type = 'character_rating' THEN crv.content
            END as activity_text,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN urv.id
                WHEN al.activity_type = 'character_rating' THEN crv.id
            END as review_id,
            CASE
                WHEN al.activity_type = 'anime_rating' THEN ur.created_at
                WHEN al.activity_type = 'character_rating' THEN cr.created_at
            END as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus.otaku_score, 0) as activity_otaku_score,
            (SELECT COUNT(*) FROM activity_likes WHERE activity_type = al.activity_type AND activity_user_id = al.activity_user_id AND item_id = al.item_id) as activity_likes_count,
            (SELECT COUNT(*) FROM activity_comments WHERE activity_type = al.activity_type AND activity_user_id = al.activity_user_id AND item_id = al.item_id) as activity_comments_count,
            (SELECT COUNT(*) FROM activity_likes WHERE user_id = ? AND activity_type = al.activity_type AND activity_user_id = al.activity_user_id AND item_id = al.item_id) > 0 as user_has_liked
        FROM activity_likes al
        JOIN users u ON al.user_id = u.id
        JOIN users au ON al.activity_user_id = au.id
        LEFT JOIN user_stats aus ON au.id = aus.user_id
        LEFT JOIN anime a ON al.activity_type = 'anime_rating' AND al.item_id = a.id
        LEFT JOIN character c ON al.activity_type = 'character_rating' AND al.item_id = c.id
        LEFT JOIN anime_character ac ON al.activity_type = 'character_rating' AND c.id = ac.character_id
        LEFT JOIN anime char_anime ON ac.anime_id = char_anime.id
        LEFT JOIN user_ratings ur ON al.activity_type = 'anime_rating'
            AND ur.user_id = al.activity_user_id AND ur.anime_id = al.item_id
        LEFT JOIN character_ratings cr ON al.activity_type = 'character_rating'
            AND cr.user_id = al.activity_user_id AND cr.character_id = al.item_id
        LEFT JOIN user_reviews urv ON al.activity_type = 'anime_rating'
            AND urv.user_id = al.activity_user_id AND urv.anime_id = al.item_id
        LEFT JOIN character_reviews crv ON al.activity_type = 'character_rating'
            AND crv.user_id = al.activity_user_id AND crv.character_id = al.item_id
        WHERE al.activity_user_id = ?
            AND al.activity_type IN ('anime_rating', 'character_rating')
            AND al.user_id != ?
        """

        # 2. 댓글 알림 가져오기 - activity_comments (평가에 달린 댓글)
        comment_query = """
        SELECT
            'comment' as notification_type,
            ac.created_at as notification_time,
            ac.activity_type,
            ac.activity_user_id,
            ac.item_id,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN COALESCE(a.title_korean, a.title_romaji, a.title_english)
                WHEN ac.activity_type = 'character_rating' THEN c.name_full
            END as item_title,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN a.cover_image_url
                WHEN ac.activity_type = 'character_rating' THEN c.image_url
            END as item_image,
            CASE
                WHEN ac.activity_type = 'character_rating' THEN char_anime2.id
                ELSE NULL
            END as anime_id,
            CASE
                WHEN ac.activity_type = 'character_rating' THEN char_anime2.title_romaji
                ELSE NULL
            END as anime_title,
            CASE
                WHEN ac.activity_type = 'character_rating' THEN char_anime2.title_korean
                ELSE NULL
            END as anime_title_korean,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN ur.rating
                WHEN ac.activity_type = 'character_rating' THEN cr.rating
            END as my_rating,
            ac.content as comment_content,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN urv.content
                WHEN ac.activity_type = 'character_rating' THEN crv.content
            END as activity_text,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN urv.id
                WHEN ac.activity_type = 'character_rating' THEN crv.id
            END as review_id,
            CASE
                WHEN ac.activity_type = 'anime_rating' THEN ur.created_at
                WHEN ac.activity_type = 'character_rating' THEN cr.created_at
            END as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus2.otaku_score, 0) as activity_otaku_score,
            (SELECT COUNT(*) FROM activity_likes WHERE activity_type = ac.activity_type AND activity_user_id = ac.activity_user_id AND item_id = ac.item_id) as activity_likes_count,
            (SELECT COUNT(*) FROM activity_comments WHERE activity_type = ac.activity_type AND activity_user_id = ac.activity_user_id AND item_id = ac.item_id) as activity_comments_count,
            (SELECT COUNT(*) FROM activity_likes WHERE user_id = ? AND activity_type = ac.activity_type AND activity_user_id = ac.activity_user_id AND item_id = ac.item_id) > 0 as user_has_liked
        FROM activity_comments ac
        JOIN users u ON ac.user_id = u.id
        JOIN users au ON ac.activity_user_id = au.id
        LEFT JOIN user_stats aus2 ON au.id = aus2.user_id
        LEFT JOIN anime a ON ac.activity_type = 'anime_rating' AND ac.item_id = a.id
        LEFT JOIN character c ON ac.activity_type = 'character_rating' AND ac.item_id = c.id
        LEFT JOIN anime_character ac2 ON ac.activity_type = 'character_rating' AND c.id = ac2.character_id
        LEFT JOIN anime char_anime2 ON ac2.anime_id = char_anime2.id
        LEFT JOIN user_ratings ur ON ac.activity_type = 'anime_rating'
            AND ur.user_id = ac.activity_user_id AND ur.anime_id = ac.item_id
        LEFT JOIN character_ratings cr ON ac.activity_type = 'character_rating'
            AND cr.user_id = ac.activity_user_id AND cr.character_id = ac.item_id
        LEFT JOIN user_reviews urv ON ac.activity_type = 'anime_rating'
            AND urv.user_id = ac.activity_user_id AND urv.anime_id = ac.item_id
        LEFT JOIN character_reviews crv ON ac.activity_type = 'character_rating'
            AND crv.user_id = ac.activity_user_id AND crv.character_id = ac.item_id
        WHERE ac.activity_user_id = ?
            AND ac.parent_comment_id IS NULL
            AND ac.activity_type IN ('anime_rating', 'character_rating')
            AND ac.user_id != ?
        """

        # 3. review_comments에서 댓글 알림 가져오기 (리뷰에 달린 댓글)
        review_comment_query = """
        SELECT
            'comment' as notification_type,
            rc.created_at as notification_time,
            CASE
                WHEN rc.review_type = 'anime' THEN 'anime_rating'
                WHEN rc.review_type = 'character' THEN 'character_rating'
            END as activity_type,
            CASE
                WHEN rc.review_type = 'anime' THEN urv.user_id
                WHEN rc.review_type = 'character' THEN crv.user_id
            END as activity_user_id,
            CASE
                WHEN rc.review_type = 'anime' THEN urv.anime_id
                WHEN rc.review_type = 'character' THEN crv.character_id
            END as item_id,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            CASE
                WHEN rc.review_type = 'anime' THEN COALESCE(a.title_korean, a.title_romaji, a.title_english)
                WHEN rc.review_type = 'character' THEN c.name_full
            END as item_title,
            CASE
                WHEN rc.review_type = 'anime' THEN a.cover_image_url
                WHEN rc.review_type = 'character' THEN c.image_url
            END as item_image,
            CASE
                WHEN rc.review_type = 'character' THEN char_anime3.id
                ELSE NULL
            END as anime_id,
            CASE
                WHEN rc.review_type = 'character' THEN char_anime3.title_romaji
                ELSE NULL
            END as anime_title,
            CASE
                WHEN rc.review_type = 'character' THEN char_anime3.title_korean
                ELSE NULL
            END as anime_title_korean,
            CASE
                WHEN rc.review_type = 'anime' THEN ur.rating
                WHEN rc.review_type = 'character' THEN cr.rating
            END as my_rating,
            rc.content as comment_content,
            CASE
                WHEN rc.review_type = 'anime' THEN urv.content
                WHEN rc.review_type = 'character' THEN crv.content
            END as activity_text,
            CASE
                WHEN rc.review_type = 'anime' THEN urv.id
                WHEN rc.review_type = 'character' THEN crv.id
            END as review_id,
            CASE
                WHEN rc.review_type = 'anime' THEN urv.created_at
                WHEN rc.review_type = 'character' THEN crv.created_at
            END as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus3.otaku_score, 0) as activity_otaku_score,
            0 as activity_likes_count,
            (SELECT COUNT(*) FROM review_comments WHERE review_id = rc.review_id AND review_type = rc.review_type) as activity_comments_count,
            0 as user_has_liked
        FROM review_comments rc
        JOIN users u ON rc.user_id = u.id
        LEFT JOIN user_reviews urv ON rc.review_type = 'anime' AND rc.review_id = urv.id
        LEFT JOIN character_reviews crv ON rc.review_type = 'character' AND rc.review_id = crv.id
        LEFT JOIN users au ON (rc.review_type = 'anime' AND au.id = urv.user_id) OR (rc.review_type = 'character' AND au.id = crv.user_id)
        LEFT JOIN user_stats aus3 ON au.id = aus3.user_id
        LEFT JOIN anime a ON rc.review_type = 'anime' AND urv.anime_id = a.id
        LEFT JOIN character c ON rc.review_type = 'character' AND crv.character_id = c.id
        LEFT JOIN anime_character ac3 ON rc.review_type = 'character' AND c.id = ac3.character_id
        LEFT JOIN anime char_anime3 ON ac3.anime_id = char_anime3.id
        LEFT JOIN user_ratings ur ON rc.review_type = 'anime' AND ur.user_id = urv.user_id AND ur.anime_id = urv.anime_id
        LEFT JOIN character_ratings cr ON rc.review_type = 'character' AND cr.user_id = crv.user_id AND cr.character_id = crv.character_id
        WHERE ((rc.review_type = 'anime' AND urv.user_id = ?) OR (rc.review_type = 'character' AND crv.user_id = ?))
            AND rc.parent_comment_id IS NULL
            AND rc.user_id != ?
        """

        # 좋아요 알림
        like_results = db.execute_query(like_query, (current_user.id, current_user.id, current_user.id))
        print(f"[Notifications API] Found {len(like_results)} like notifications")
        for row in like_results:
            notifications.append({
                'type': row[0],
                'time': row[1],
                'activity_type': row[2],
                'target_user_id': row[3],
                'item_id': row[4],
                'actor_user_id': row[5],
                'actor_username': row[6],
                'actor_display_name': row[7],
                'actor_avatar_url': row[8],
                'item_title': row[9],
                'item_image': row[10],
                'anime_id': row[11],
                'anime_title': row[12],
                'anime_title_korean': row[13],
                'my_rating': row[14],
                'comment_content': None,
                'activity_text': row[15],
                'review_id': row[16],
                'activity_created_at': row[17],
                'activity_username': row[18],
                'activity_display_name': row[19],
                'activity_avatar_url': row[20],
                'activity_otaku_score': row[21],
                'activity_likes_count': row[22],
                'activity_comments_count': row[23],
                'user_has_liked': row[24]
            })

        # activity_comments 댓글 알림
        comment_results = db.execute_query(comment_query, (current_user.id, current_user.id, current_user.id))
        print(f"[Notifications API] Found {len(comment_results)} activity comment notifications")
        for row in comment_results:
            notifications.append({
                'type': row[0],
                'time': row[1],
                'activity_type': row[2],
                'target_user_id': row[3],
                'item_id': row[4],
                'actor_user_id': row[5],
                'actor_username': row[6],
                'actor_display_name': row[7],
                'actor_avatar_url': row[8],
                'item_title': row[9],
                'item_image': row[10],
                'anime_id': row[11],
                'anime_title': row[12],
                'anime_title_korean': row[13],
                'my_rating': row[14],
                'comment_content': row[15],
                'activity_text': row[16],
                'review_id': row[17],
                'activity_created_at': row[18],
                'activity_username': row[19],
                'activity_display_name': row[20],
                'activity_avatar_url': row[21],
                'activity_otaku_score': row[22],
                'activity_likes_count': row[23],
                'activity_comments_count': row[24],
                'user_has_liked': row[25]
            })

        # review_comments 댓글 알림
        review_comment_results = db.execute_query(review_comment_query, (current_user.id, current_user.id, current_user.id))
        print(f"[Notifications API] Found {len(review_comment_results)} review comment notifications")
        for row in review_comment_results:
            notifications.append({
                'type': row[0],
                'time': row[1],
                'activity_type': row[2],
                'target_user_id': row[3],
                'item_id': row[4],
                'actor_user_id': row[5],
                'actor_username': row[6],
                'actor_display_name': row[7],
                'actor_avatar_url': row[8],
                'item_title': row[9],
                'item_image': row[10],
                'anime_id': row[11],
                'anime_title': row[12],
                'anime_title_korean': row[13],
                'my_rating': row[14],
                'comment_content': row[15],
                'activity_text': row[16],
                'review_id': row[17],
                'activity_created_at': row[18],
                'activity_username': row[19],
                'activity_display_name': row[20],
                'activity_avatar_url': row[21],
                'activity_otaku_score': row[22],
                'activity_likes_count': row[23],
                'activity_comments_count': row[24],
                'user_has_liked': row[25]
            })

        # 시간 순으로 정렬
        notifications.sort(key=lambda x: x['time'], reverse=True)

        # Pagination
        total = len(notifications)
        notifications = notifications[offset:offset+limit]

        print(f"[Notifications API] Returning {len(notifications)} notifications (total: {total})")

        return {
            'items': notifications,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    except Exception as e:
        print(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@router.get("/unread-count")
async def get_unread_count(
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    읽지 않은 알림 개수 반환
    user의 last_notification_check 이후 생성된 알림 개수
    """
    try:
        print(f"[Notifications API] Getting unread count for user {current_user.id}")

        # Get user's last notification check time
        user_row = db.execute_query(
            "SELECT last_notification_check FROM users WHERE id = ?",
            (current_user.id,),
            fetch_one=True
        )

        last_check = user_row[0] if user_row and user_row[0] else '2000-01-01 00:00:00'
        print(f"[Notifications API] Last check: {last_check}")

        # Count activity_likes after last_check (좋아요 알림)
        like_count_anime = len(db.execute_query(
            """
            SELECT al.id FROM activity_likes al
            WHERE al.activity_user_id = ?
            AND al.activity_type IN ('anime_rating', 'anime_review')
            AND al.created_at > ?
            AND al.user_id != ?
            """,
            (current_user.id, last_check, current_user.id)
        ))

        like_count_char = len(db.execute_query(
            """
            SELECT al.id FROM activity_likes al
            WHERE al.activity_user_id = ?
            AND al.activity_type IN ('character_rating', 'character_review')
            AND al.created_at > ?
            AND al.user_id != ?
            """,
            (current_user.id, last_check, current_user.id)
        ))

        # Count activity_comments after last_check (평점 댓글 알림)
        comment_count_activity = len(db.execute_query(
            """
            SELECT ac.id FROM activity_comments ac
            WHERE ac.activity_user_id = ?
            AND ac.activity_type IN ('anime_rating', 'character_rating')
            AND ac.created_at > ?
            AND ac.user_id != ?
            AND ac.parent_comment_id IS NULL
            """,
            (current_user.id, last_check, current_user.id)
        ))

        # Count review_comments after last_check (리뷰 댓글 알림)
        # Anime reviews
        comment_count_anime_review = len(db.execute_query(
            """
            SELECT rc.id FROM review_comments rc
            JOIN user_reviews ur ON rc.review_id = ur.id
            WHERE rc.review_type = 'anime'
            AND ur.user_id = ?
            AND rc.created_at > ?
            AND rc.user_id != ?
            AND rc.parent_comment_id IS NULL
            """,
            (current_user.id, last_check, current_user.id)
        ))

        # Character reviews
        comment_count_char_review = len(db.execute_query(
            """
            SELECT rc.id FROM review_comments rc
            JOIN character_reviews cr ON rc.review_id = cr.id
            WHERE rc.review_type = 'character'
            AND cr.user_id = ?
            AND rc.created_at > ?
            AND rc.user_id != ?
            AND rc.parent_comment_id IS NULL
            """,
            (current_user.id, last_check, current_user.id)
        ))

        total_count = (like_count_anime + like_count_char +
                      comment_count_activity +
                      comment_count_anime_review + comment_count_char_review)

        print(f"[Notifications API] Unread count: {total_count} (likes: {like_count_anime + like_count_char}, comments: {comment_count_activity + comment_count_anime_review + comment_count_char_review})")

        return {"count": total_count}

    except Exception as e:
        print(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")


@router.post("/mark-read")
async def mark_notifications_read(
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    알림을 읽음 처리
    현재 시간으로 last_notification_check 업데이트
    """
    try:
        print(f"[Notifications API] Marking notifications as read for user {current_user.id}")

        from datetime import datetime
        current_time = datetime.utcnow().isoformat()

        db.execute_query(
            "UPDATE users SET last_notification_check = ? WHERE id = ?",
            (current_time, current_user.id)
        )

        print(f"[Notifications API] Updated last_notification_check to {current_time}")

        return {"success": True, "timestamp": current_time}

    except Exception as e:
        print(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")
