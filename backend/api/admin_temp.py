# Add this to admin.py temporarily
@router.get("/user-activities/{user_id}")
def get_user_activities_count(user_id: int):
    """Get activity counts for a specific user"""
    from database import get_db
    db = get_db()
    
    # Count all activity types
    anime_ratings = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'anime_rating'",
        (user_id,)
    )
    
    character_ratings = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'character_rating'",
        (user_id,)
    )
    
    user_posts = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'user_post'",
        (user_id,)
    )
    
    total = db.execute_query(
        "SELECT COUNT(*) FROM activities WHERE user_id = ?",
        (user_id,)
    )
    
    return {
        "user_id": user_id,
        "anime_ratings": anime_ratings[0][0] if anime_ratings else 0,
        "character_ratings": character_ratings[0][0] if character_ratings else 0,
        "user_posts": user_posts[0][0] if user_posts else 0,
        "total": total[0][0] if total else 0
    }
