"""
Admin API - Temporary endpoints for database migrations
임시 관리자 API
"""
from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter()


@router.post("/verify-all-users")
def verify_all_users_endpoint():
    """
    Verify all existing users (temporary migration endpoint)
    기존 사용자 모두 인증 완료 처리 (임시 마이그레이션 엔드포인트)
    """
    try:
        # Check current status
        rows = db.execute_query(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
        )
        total = rows[0][0] if rows else 0
        verified_before = rows[0][1] if rows else 0
        unverified_before = total - verified_before

        # Update all users to verified
        updated = db.execute_update(
            """
            UPDATE users
            SET is_verified = 1,
                verification_token = NULL,
                verification_token_expires = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE is_verified = 0 OR is_verified IS NULL
            """
        )

        # Check updated status
        rows = db.execute_query(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified FROM users"
        )
        verified_after = rows[0][1] if rows else 0

        return {
            "message": "All users verified successfully",
            "total_users": total,
            "verified_before": verified_before,
            "unverified_before": unverified_before,
            "verified_after": verified_after,
            "updated": updated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify users: {str(e)}")


@router.get("/users-status")
def get_users_status():
    """
    Get users verification status
    사용자 인증 상태 확인
    """
    try:
        rows = db.execute_query(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN is_verified = 0 OR is_verified IS NULL THEN 1 ELSE 0 END) as unverified
            FROM users
            """
        )

        total = rows[0][0] if rows else 0
        verified = rows[0][1] if rows else 0
        unverified = rows[0][2] if rows else 0

        # Get sample unverified users
        unverified_users = db.execute_query(
            "SELECT id, username, email, is_verified FROM users WHERE is_verified = 0 OR is_verified IS NULL LIMIT 5"
        )

        unverified_list = [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "is_verified": row[3]
            }
            for row in unverified_users
        ]

        return {
            "total_users": total,
            "verified": verified,
            "unverified": unverified,
            "unverified_sample": unverified_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/add-activities-metadata")
def add_activities_metadata():
    """Add metadata column to activities table"""
    try:
        # Check if column exists
        columns_info = db.execute_query("PRAGMA table_info(activities)")
        columns = [row['name'] for row in columns_info]

        if 'metadata' not in columns:
            db.execute_update("ALTER TABLE activities ADD COLUMN metadata TEXT")
            return {"success": True, "message": "metadata column added successfully"}
        else:
            return {"success": True, "message": "metadata column already exists"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/check-rank-promotions")
def check_rank_promotions():
    """Check rank promotion activities in database"""
    try:
        # Get all rank promotions
        promotions = db.execute_query("""
            SELECT user_id, username, activity_time, metadata
            FROM activities
            WHERE activity_type = 'rank_promotion'
            ORDER BY activity_time DESC
            LIMIT 50
        """)

        promotion_list = [
            {
                "user_id": row[0],
                "username": row[1],
                "activity_time": row[2],
                "metadata": row[3]
            }
            for row in promotions
        ]

        # Get total count
        count_row = db.execute_query("SELECT COUNT(*) FROM activities WHERE activity_type = 'rank_promotion'")
        total = count_row[0][0] if count_row else 0

        return {
            "total": total,
            "promotions": promotion_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/check-user-followers/{user_id}")
def check_user_followers(user_id: int):
    """Check user's follower and following counts"""
    try:
        # Get follower count
        follower_rows = db.execute_query("SELECT COUNT(*) FROM user_follows WHERE following_id = ?", (user_id,))
        follower_count = follower_rows[0][0] if follower_rows else 0

        # Get following count
        following_rows = db.execute_query("SELECT COUNT(*) FROM user_follows WHERE follower_id = ?", (user_id,))
        following_count = following_rows[0][0] if following_rows else 0

        # Get actual follows
        followers = db.execute_query("""
            SELECT follower_id, (SELECT username FROM users WHERE id = follower_id) as username
            FROM user_follows WHERE following_id = ?
        """, (user_id,))

        following = db.execute_query("""
            SELECT following_id, (SELECT username FROM users WHERE id = following_id) as username
            FROM user_follows WHERE follower_id = ?
        """, (user_id,))

        return {
            "user_id": user_id,
            "follower_count": follower_count,
            "following_count": following_count,
            "followers": [{"id": row[0], "username": row[1]} for row in followers],
            "following": [{"id": row[0], "username": row[1]} for row in following]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/check-user-activities/{user_id}")
def check_user_activities(user_id: int):
    """Check user's activities and calculate otaku score"""
    try:
        # Get user's current otaku score
        user_stats = db.execute_query("SELECT otaku_score FROM user_stats WHERE user_id = ?", (user_id,))
        current_score = user_stats[0][0] if user_stats else 0

        # Count activities
        anime_ratings = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'anime_rating'", (user_id,))
        anime_reviews = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'anime_review'", (user_id,))
        character_ratings = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'character_rating'", (user_id,))
        character_reviews = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_type = 'character_review'", (user_id,))

        anime_rating_count = anime_ratings[0][0] if anime_ratings else 0
        anime_review_count = anime_reviews[0][0] if anime_reviews else 0
        character_rating_count = character_ratings[0][0] if character_ratings else 0
        character_review_count = character_reviews[0][0] if character_reviews else 0

        calculated_score = (anime_rating_count * 2) + (character_rating_count * 1) + ((anime_review_count + character_review_count) * 5)

        # Get all activities chronologically
        activities = db.execute_query("""
            SELECT activity_type, activity_time
            FROM activities
            WHERE user_id = ? AND activity_type IN ('anime_rating', 'anime_review', 'character_rating', 'character_review')
            ORDER BY activity_time ASC
            LIMIT 20
        """, (user_id,))

        return {
            "user_id": user_id,
            "current_otaku_score": current_score,
            "calculated_score": calculated_score,
            "anime_ratings": anime_rating_count,
            "anime_reviews": anime_review_count,
            "character_ratings": character_rating_count,
            "character_reviews": character_review_count,
            "first_20_activities": [{"type": row[0], "time": row[1]} for row in activities]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/delete-all-rank-promotions")
def delete_all_rank_promotions():
    """Delete all rank_promotion activities"""
    try:
        deleted = db.execute_update("DELETE FROM activities WHERE activity_type = 'rank_promotion'")
        return {
            "success": True,
            "deleted": deleted,
            "message": f"Deleted {deleted} rank promotion activities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/backfill-rank-promotions")
def backfill_rank_promotions():
    """Backfill past rank promotion activities"""
    from datetime import datetime
    import json

    def get_rank_info(otaku_score: float):
        """Get rank name and level from otaku score (matches frontend otakuLevels.js)"""
        if otaku_score <= 49:
            return "루키", 1
        elif otaku_score <= 119:
            return "헌터", 2
        elif otaku_score <= 219:
            return "워리어", 3
        elif otaku_score <= 349:
            return "나이트", 4
        elif otaku_score <= 549:
            return "마스터", 5
        elif otaku_score <= 799:
            return "하이마스터", 6
        elif otaku_score <= 1099:
            return "그랜드마스터", 7
        elif otaku_score <= 1449:
            return "오타쿠", 8
        elif otaku_score <= 1799:
            return "오타쿠 킹", 9
        else:
            return "오타쿠 갓", 10

    try:
        # Get all users
        users = db.execute_query("SELECT id, username, display_name, avatar_url FROM users")

        total_promotions = 0
        processed_users = []

        for user in users:
            user_id = user['id']
            username = user['username']
            display_name = user['display_name']
            avatar_url = user['avatar_url']

            # Get all activities from source tables in chronological order
            activities = db.execute_query("""
                SELECT 'anime_rating' as activity_type, updated_at as activity_time
                FROM user_ratings
                WHERE user_id = ? AND status = 'RATED' AND rating IS NOT NULL

                UNION ALL

                SELECT 'anime_review' as activity_type, created_at as activity_time
                FROM user_reviews
                WHERE user_id = ?

                UNION ALL

                SELECT 'character_rating' as activity_type, updated_at as activity_time
                FROM character_ratings
                WHERE user_id = ? AND rating IS NOT NULL

                UNION ALL

                SELECT 'character_review' as activity_type, created_at as activity_time
                FROM character_reviews
                WHERE user_id = ?

                ORDER BY activity_time ASC
            """, (user_id, user_id, user_id, user_id))

            # Calculate otaku_score at each point in time
            anime_ratings_count = 0
            character_ratings_count = 0
            reviews_count = 0

            prev_rank = None
            prev_level = None
            user_promotions = 0

            for activity in activities:
                activity_time = activity['activity_time']
                activity_type = activity['activity_type']

                # Update counts
                if activity_type == 'anime_rating':
                    anime_ratings_count += 1
                elif activity_type == 'character_rating':
                    character_ratings_count += 1
                elif activity_type in ('anime_review', 'character_review'):
                    reviews_count += 1

                # Calculate current otaku_score
                otaku_score = (anime_ratings_count * 2) + (character_ratings_count * 1) + (reviews_count * 5)

                # Get current rank
                current_rank, current_level = get_rank_info(otaku_score)

                # Check if rank changed
                if prev_rank is not None:
                    if (current_rank != prev_rank) or (current_rank == prev_rank and current_level > prev_level):
                        # Check if this promotion already exists
                        existing = db.execute_query("""
                            SELECT id FROM activities
                            WHERE activity_type = 'rank_promotion'
                              AND user_id = ?
                              AND activity_time = ?
                        """, (user_id, activity_time))

                        if not existing:
                            # Create metadata
                            metadata = json.dumps({
                                'old_rank': prev_rank,
                                'old_level': prev_level,
                                'new_rank': current_rank,
                                'new_level': current_level,
                                'otaku_score': otaku_score
                            })

                            # Insert rank promotion activity
                            db.execute_insert("""
                                INSERT INTO activities (
                                    activity_type, user_id, username, display_name, avatar_url,
                                    item_id, metadata, activity_time, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                'rank_promotion',
                                user_id,
                                username,
                                display_name,
                                avatar_url,
                                None,
                                metadata,
                                activity_time,
                                datetime.now().isoformat(),
                                datetime.now().isoformat()
                            ))

                            user_promotions += 1
                            total_promotions += 1

                # Update previous rank
                prev_rank = current_rank
                prev_level = current_level

            if user_promotions > 0:
                processed_users.append({
                    'user_id': user_id,
                    'username': username,
                    'display_name': display_name,
                    'promotions': user_promotions
                })

        return {
            "success": True,
            "total_promotions": total_promotions,
            "processed_users": processed_users
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
