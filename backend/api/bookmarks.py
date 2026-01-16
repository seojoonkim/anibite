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
    from services.activity_service import get_activity_by_id

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
    print(f"[Bookmarks] Activity IDs: {activity_ids}")

    # Get full activity details using activity_service
    # This returns activities with all engagement data (likes, comments, etc.)
    activities = []
    for activity_id in activity_ids:
        try:
            activity = get_activity_by_id(activity_id, current_user.id)
            if activity:
                # Add bookmarked flag
                activity['user_bookmarked'] = True
                activities.append(activity)
                print(f"[Bookmarks] Loaded activity {activity_id}")
            else:
                print(f"[Bookmarks] Activity {activity_id} not found")
        except Exception as e:
            print(f"[Bookmarks] Error loading bookmarked activity {activity_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"[Bookmarks] Returning {len(activities)} activities")

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
