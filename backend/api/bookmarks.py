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
def get_bookmarks(current_user: UserResponse = Depends(get_current_user)):
    """
    Get all bookmarks for current user
    현재 사용자의 모든 북마크 조회
    """
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
