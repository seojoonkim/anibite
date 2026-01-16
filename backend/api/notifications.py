"""
Notifications API - Simplified version
사용자 알림 관리 (activities 테이블 기반)
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
    - 내가 작성한 활동에 다른 사용자가 좋아요나 댓글을 남긴 경우
    """
    notifications = []

    try:
        print(f"[Notifications API] Loading notifications for user {current_user.id} ({current_user.username})")

        # 1. 좋아요 알림 가져오기
        like_query = """
        SELECT
            'like' as notification_type,
            al.created_at as notification_time,
            a.activity_type,
            a.user_id as target_user_id,
            a.item_id,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            a.item_title,
            a.item_title_korean,
            a.item_image,
            a.anime_id,
            a.anime_title,
            a.anime_title_korean,
            a.rating as my_rating,
            a.review_content as activity_text,
            a.review_id,
            a.activity_time as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus.otaku_score, 0) as activity_otaku_score,
            0 as activity_likes_count,
            0 as activity_comments_count,
            0 as user_has_liked
        FROM activity_likes al
        JOIN activities a ON al.activity_id = a.id
        JOIN users u ON al.user_id = u.id
        JOIN users au ON a.user_id = au.id
        LEFT JOIN user_stats aus ON au.id = aus.user_id
        WHERE a.user_id = ?
            AND al.user_id != ?
        ORDER BY al.created_at DESC
        LIMIT ? OFFSET ?
        """

        like_results = db.execute_query(like_query, (current_user.id, current_user.id, limit, offset))
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
                'item_title_korean': row[10],
                'item_image': row[11],
                'anime_id': row[12],
                'anime_title': row[13],
                'anime_title_korean': row[14],
                'my_rating': row[15],
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

        # 2. 댓글 알림 가져오기
        comment_query = """
        SELECT
            'comment' as notification_type,
            ac.created_at as notification_time,
            a.activity_type,
            a.user_id as target_user_id,
            a.item_id,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            a.item_title,
            a.item_title_korean,
            a.item_image,
            a.anime_id,
            a.anime_title,
            a.anime_title_korean,
            a.rating as my_rating,
            a.review_content as activity_text,
            a.review_id,
            a.activity_time as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus.otaku_score, 0) as activity_otaku_score,
            0 as activity_likes_count,
            0 as activity_comments_count,
            0 as user_has_liked,
            ac.content as comment_text
        FROM activity_comments ac
        JOIN activities a ON ac.activity_id = a.id
        JOIN users u ON ac.user_id = u.id
        JOIN users au ON a.user_id = au.id
        LEFT JOIN user_stats aus ON au.id = aus.user_id
        WHERE a.user_id = ?
            AND ac.user_id != ?
            AND ac.parent_comment_id IS NULL
        ORDER BY ac.created_at DESC
        LIMIT ? OFFSET ?
        """

        comment_results = db.execute_query(comment_query, (current_user.id, current_user.id, limit, offset))
        print(f"[Notifications API] Found {len(comment_results)} comment notifications")

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
                'item_title_korean': row[10],
                'item_image': row[11],
                'anime_id': row[12],
                'anime_title': row[13],
                'anime_title_korean': row[14],
                'my_rating': row[15],
                'activity_text': row[16],
                'review_id': row[17],
                'activity_created_at': row[18],
                'activity_username': row[19],
                'activity_display_name': row[20],
                'activity_avatar_url': row[21],
                'activity_otaku_score': row[22],
                'activity_likes_count': row[23],
                'activity_comments_count': row[24],
                'user_has_liked': row[25],
                'comment_text': row[26]
            })

        # Sort all notifications by time
        notifications.sort(key=lambda x: x['time'], reverse=True)

        # Apply limit
        notifications = notifications[:limit]

        print(f"[Notifications API] Returning {len(notifications)} total notifications")

        return {
            'items': notifications,
            'total': len(notifications)
        }

    except Exception as e:
        print(f"Error fetching notifications: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """알림 개수 확인"""
    try:
        print(f"[Notifications API] Getting unread count for user {current_user.id}")

        # Get last check time
        last_check_query = "SELECT last_notification_check FROM users WHERE id = ?"
        last_check_result = db.execute_query(last_check_query, (current_user.id,), fetch_one=True)
        last_check = last_check_result['last_notification_check'] if last_check_result else '2000-01-01 00:00:00'

        print(f"[Notifications API] Last check: {last_check}")

        # Count likes
        likes_query = """
        SELECT COUNT(*) as count
        FROM activity_likes al
        JOIN activities a ON al.activity_id = a.id
        WHERE a.user_id = ?
            AND al.user_id != ?
            AND al.created_at > ?
        """
        likes_result = db.execute_query(likes_query, (current_user.id, current_user.id, last_check), fetch_one=True)
        likes_count = likes_result['count'] if likes_result else 0

        # Count comments
        comments_query = """
        SELECT COUNT(*) as count
        FROM activity_comments ac
        JOIN activities a ON ac.activity_id = a.id
        WHERE a.user_id = ?
            AND ac.user_id != ?
            AND ac.parent_comment_id IS NULL
            AND ac.created_at > ?
        """
        comments_result = db.execute_query(comments_query, (current_user.id, current_user.id, last_check), fetch_one=True)
        comments_count = comments_result['count'] if comments_result else 0

        total_count = likes_count + comments_count
        print(f"[Notifications API] Unread count: {total_count} (likes: {likes_count}, comments: {comments_count})")

        return {
            'unread_count': total_count,
            'likes_count': likes_count,
            'comments_count': comments_count
        }

    except Exception as e:
        print(f"Error getting unread count: {e}")
        return {
            'unread_count': 0,
            'likes_count': 0,
            'comments_count': 0
        }


@router.post("/mark-read")
async def mark_notifications_read(
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """알림을 읽음으로 표시"""
    try:
        current_time = datetime.now().isoformat()
        db.execute_update(
            "UPDATE users SET last_notification_check = ? WHERE id = ?",
            (current_time, current_user.id)
        )
        return {'message': 'Notifications marked as read'}
    except Exception as e:
        print(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
