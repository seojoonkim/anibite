"""
Notifications API - Database-driven notifications
전용 notifications 테이블 사용
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
    알림 목록 조회 (notifications 테이블에서 직접 가져옴)
    """
    try:
        print(f"[Notifications API] Loading notifications for user {current_user.id}")

        query = """
        SELECT
            n.id as notification_id,
            n.type,
            n.created_at,
            n.is_read,
            n.content as comment_text,
            u.id as actor_user_id,
            u.username as actor_username,
            u.display_name as actor_display_name,
            u.avatar_url as actor_avatar_url,
            COALESCE(us.otaku_score, 0) as actor_otaku_score,
            a.id as activity_id,
            a.activity_type,
            a.user_id as target_user_id,
            a.item_id,
            a.item_title,
            a.item_title_korean,
            a.item_image,
            a.anime_id,
            a.anime_title,
            a.anime_title_korean,
            a.rating as my_rating,
            a.review_content as activity_text,
            NULL as review_id,
            a.activity_time as activity_created_at,
            au.username as activity_username,
            au.display_name as activity_display_name,
            au.avatar_url as activity_avatar_url,
            COALESCE(aus.otaku_score, 0) as activity_otaku_score,
            COALESCE(likes.count, 0) as activity_likes_count,
            COALESCE(comments.count, 0) as activity_comments_count,
            CASE WHEN user_like.activity_id IS NOT NULL THEN 1 ELSE 0 END as user_has_liked
        FROM notifications n
        JOIN users u ON n.actor_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        JOIN activities a ON n.activity_id = a.id
        JOIN users au ON a.user_id = au.id
        LEFT JOIN user_stats aus ON au.id = aus.user_id
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_likes
            GROUP BY activity_id
        ) likes ON likes.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_comments
            GROUP BY activity_id
        ) comments ON comments.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id
            FROM activity_likes
            WHERE user_id = ?
        ) user_like ON user_like.activity_id = a.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
        LIMIT ? OFFSET ?
        """

        results = db.execute_query(query, (current_user.id, current_user.id, limit, offset))
        print(f"[Notifications API] Found {len(results)} notifications")

        notifications = []
        for row in results:
            notifications.append({
                'notification_id': row[0],
                'type': row[1],
                'time': row[2],
                'is_read': row[3],
                'comment_text': row[4],
                'actor_user_id': row[5],
                'actor_username': row[6],
                'actor_display_name': row[7],
                'actor_avatar_url': row[8],
                'actor_otaku_score': row[9],
                'activity_id': row[10],
                'activity_type': row[11],
                'target_user_id': row[12],
                'item_id': row[13],
                'item_title': row[14],
                'item_title_korean': row[15],
                'item_image': row[16],
                'anime_id': row[17],
                'anime_title': row[18],
                'anime_title_korean': row[19],
                'my_rating': row[20],
                'activity_text': row[21],
                'review_id': row[22],
                'activity_created_at': row[23],
                'activity_username': row[24],
                'activity_display_name': row[25],
                'activity_avatar_url': row[26],
                'activity_otaku_score': row[27],
                'activity_likes_count': row[28],
                'activity_comments_count': row[29],
                'user_has_liked': row[30]
            })

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
    """읽지 않은 알림 개수"""
    try:
        query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE"
        result = db.execute_query(query, (current_user.id,), fetch_one=True)
        count = result['count'] if result else 0

        print(f"[Notifications API] Unread count for user {current_user.id}: {count}")

        return {
            'unread_count': count
        }

    except Exception as e:
        print(f"Error getting unread count: {e}")
        return {'unread_count': 0}


@router.post("/mark-read")
async def mark_notifications_read(
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """모든 알림을 읽음으로 표시"""
    try:
        db.execute_update(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = ? AND is_read = FALSE",
            (current_user.id,)
        )
        return {'message': 'Notifications marked as read'}
    except Exception as e:
        print(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """특정 알림 삭제"""
    try:
        result = db.execute_update(
            "DELETE FROM notifications WHERE id = ? AND user_id = ?",
            (notification_id, current_user.id)
        )

        if result == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {'message': 'Notification deleted'}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_notification(db: Database, user_id: int, actor_id: int, notification_type: str,
                       activity_id: int, comment_id: int = None, content: str = None):
    """
    알림 생성 헬퍼 함수
    다른 API에서 호출하여 알림 생성
    """
    # 자기 자신에게는 알림 생성 안 함
    if user_id == actor_id:
        return

    try:
        # 중복 알림 체크 (같은 사람이 같은 활동에 같은 타입의 알림을 이미 만들었는지)
        check_query = """
        SELECT id FROM notifications
        WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = ?
        """
        existing = db.execute_query(
            check_query,
            (user_id, actor_id, activity_id, notification_type),
            fetch_one=True
        )

        if existing:
            # 이미 존재하면 시간만 업데이트
            db.execute_update(
                "UPDATE notifications SET created_at = CURRENT_TIMESTAMP WHERE id = ?",
                (existing['id'],)
            )
            print(f"[Notifications] Updated existing notification {existing['id']}")
        else:
            # 새 알림 생성
            db.execute_insert(
                """
                INSERT INTO notifications (user_id, actor_id, type, activity_id, comment_id, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, actor_id, notification_type, activity_id, comment_id, content)
            )
            print(f"[Notifications] Created new notification: {notification_type} for user {user_id}")

    except Exception as e:
        print(f"Error creating notification: {e}")
        # 알림 생성 실패해도 원래 작업(좋아요/댓글)은 성공해야 함
        pass


def delete_notification_by_action(db: Database, user_id: int, actor_id: int,
                                  notification_type: str, activity_id: int):
    """
    알림 삭제 헬퍼 함수
    좋아요 취소, 댓글 삭제 시 호출
    """
    try:
        db.execute_update(
            """
            DELETE FROM notifications
            WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = ?
            """,
            (user_id, actor_id, activity_id, notification_type)
        )
        print(f"[Notifications] Deleted notification: {notification_type} for user {user_id}")
    except Exception as e:
        print(f"Error deleting notification: {e}")
        pass
