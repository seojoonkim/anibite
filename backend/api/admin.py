"""
Admin API - Temporary endpoints for database maintenance
"""
from fastapi import APIRouter, HTTPException
from database import get_db

router = APIRouter()


@router.post("/cleanup-orphan-activities")
def cleanup_orphan_activities():
    """Delete orphan user_post activities where item_id is NULL"""
    db = get_db()
    
    # Check before
    before = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE activity_type = 'user_post' AND item_id IS NULL"
    )
    orphan_count = before[0][0] if before else 0
    
    # Delete orphans
    deleted = db.execute_update(
        "DELETE FROM activities WHERE activity_type = 'user_post' AND item_id IS NULL"
    )
    
    # Check after
    after = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE activity_type = 'user_post'"
    )
    remaining = after[0][0] if after else 0
    
    return {
        "orphans_found": orphan_count,
        "deleted": deleted,
        "remaining_activities": remaining
    }


@router.get("/check-activities")
def check_activities():
    """Check user_post activities status"""
    db = get_db()
    
    # Count user_posts
    posts = db.execute_query("SELECT COUNT(*) FROM user_posts")
    posts_count = posts[0][0] if posts else 0
    
    # Count activities
    activities = db.execute_query("SELECT COUNT(*) FROM activities WHERE activity_type = 'user_post'")
    activities_count = activities[0][0] if activities else 0
    
    # Count orphans
    orphans = db.execute_query("SELECT COUNT(*) FROM activities WHERE activity_type = 'user_post' AND item_id IS NULL")
    orphans_count = orphans[0][0] if orphans else 0
    
    # Get recent activities
    recent = db.execute_query(
        "SELECT user_id, item_id, activity_time FROM activities WHERE activity_type = 'user_post' ORDER BY activity_time DESC LIMIT 5"
    )
    
    return {
        "user_posts_count": posts_count,
        "activities_count": activities_count,
        "orphans_count": orphans_count,
        "recent_activities": [
            {"user_id": r[0], "item_id": r[1], "activity_time": r[2]}
            for r in recent
        ]
    }
