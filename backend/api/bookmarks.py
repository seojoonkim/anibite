"""
Bookmarks API Router
활동 북마크 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import db
from api.deps import get_current_user
from models.user import UserResponse

router = APIRouter()


@router.get("/")
def get_bookmarks(
    full: bool = False,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all bookmarks for current user
    현재 사용자의 모든 북마크 조회

    Args:
        full: If True, return full activity details. If False, return just activity IDs
    """
    if not full:
        # Return just activity IDs (for backward compatibility)
        bookmarks = db.execute_query(
            """
            SELECT activity_id, created_at
            FROM activity_bookmarks
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (current_user.id,)
        )

        return {
            'bookmarks': [
                {
                    'activity_id': b[0],
                    'created_at': b[1]
                }
                for b in bookmarks
            ]
        }

    # Return full activity details
    from services.activity_service import get_activities
    from database import get_db

    # Get bookmarked activity IDs
    bookmarked_ids = db.execute_query(
        """
        SELECT activity_id
        FROM activity_bookmarks
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (current_user.id,)
    )

    print(f"[Bookmarks] User {current_user.id} has {len(bookmarked_ids)} bookmarks")

    if not bookmarked_ids:
        return {
            'items': [],
            'total': 0
        }

    # Convert to list of IDs
    activity_ids = [row[0] for row in bookmarked_ids]

    # Get full activity details using activity_service
    # This returns activities with all engagement data (likes, comments, etc.)
    activities = []
    for activity_id in activity_ids:
        try:
            activity_data = db.execute_query(
                """
                SELECT
                    a.id,
                    a.activity_type,
                    a.user_id,
                    a.item_id,
                    a.item_title,
                    a.item_title_korean,
                    a.item_image,
                    a.anime_id,
                    a.anime_title,
                    a.anime_title_korean,
                    a.rating,
                    a.review_title,
                    a.review_content,
                    a.review_id,
                    a.is_spoiler,
                    a.activity_time,
                    a.created_at,
                    a.updated_at,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score,
                    (SELECT COUNT(*) FROM activity_likes WHERE activity_id = a.id) as likes_count,
                    (SELECT COUNT(*) FROM activity_comments WHERE activity_type = a.activity_type AND activity_user_id = a.user_id AND item_id = a.item_id) as comments_count,
                    (SELECT COUNT(*) FROM activity_likes WHERE activity_id = a.id AND user_id = ?) > 0 as user_liked
                FROM activities a
                JOIN users u ON a.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                WHERE a.id = ?
                """,
                (current_user.id, activity_id),
                fetch_one=True
            )

            if activity_data:
                activity = {
                    'id': activity_data[0],
                    'activity_type': activity_data[1],
                    'user_id': activity_data[2],
                    'item_id': activity_data[3],
                    'item_title': activity_data[4],
                    'item_title_korean': activity_data[5],
                    'item_image': activity_data[6],
                    'anime_id': activity_data[7],
                    'anime_title': activity_data[8],
                    'anime_title_korean': activity_data[9],
                    'rating': activity_data[10],
                    'review_title': activity_data[11],
                    'review_content': activity_data[12],
                    'review_id': activity_data[13],
                    'is_spoiler': bool(activity_data[14]),
                    'activity_time': activity_data[15],
                    'created_at': activity_data[16],
                    'updated_at': activity_data[17],
                    'username': activity_data[18],
                    'display_name': activity_data[19],
                    'avatar_url': activity_data[20],
                    'otaku_score': activity_data[21],
                    'likes_count': activity_data[22],
                    'comments_count': activity_data[23],
                    'user_liked': bool(activity_data[24]),
                    'is_my_activity': activity_data[2] == current_user.id,
                    'user_bookmarked': True  # Always true for bookmarked items
                }
                activities.append(activity)
        except Exception as e:
            print(f"[Bookmarks] Error loading bookmarked activity {activity_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    return {
        'items': activities,
        'total': len(activities)
    }


@router.post("/{activity_id}")
def add_bookmark(activity_id: int, current_user: UserResponse = Depends(get_current_user)):
    """
    Add activity to bookmarks
    활동을 북마크에 추가
    """
    try:
        db.execute_insert(
            """
            INSERT INTO activity_bookmarks (user_id, activity_id)
            VALUES (?, ?)
            """,
            (current_user.id, activity_id)
        )
        return {'message': 'Bookmark added successfully'}
    except Exception as e:
        # If already exists, ignore (UNIQUE constraint)
        if 'UNIQUE constraint' in str(e):
            return {'message': 'Already bookmarked'}
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{activity_id}")
def remove_bookmark(activity_id: int, current_user: UserResponse = Depends(get_current_user)):
    """
    Remove activity from bookmarks
    북마크에서 활동 제거
    """
    result = db.execute_update(
        """
        DELETE FROM activity_bookmarks
        WHERE user_id = ? AND activity_id = ?
        """,
        (current_user.id, activity_id)
    )

    if result == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return {'message': 'Bookmark removed successfully'}


@router.get("/check/{activity_id}")
def check_bookmark(activity_id: int, current_user: UserResponse = Depends(get_current_user)):
    """
    Check if activity is bookmarked
    활동이 북마크되어 있는지 확인
    """
    result = db.execute_query(
        """
        SELECT COUNT(*) FROM activity_bookmarks
        WHERE user_id = ? AND activity_id = ?
        """,
        (current_user.id, activity_id),
        fetch_one=True
    )

    return {'bookmarked': result[0] > 0}
