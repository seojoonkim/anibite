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


@router.post("/backfill-rank-promotions")
def backfill_rank_promotions():
    """Backfill past rank promotion activities"""
    from datetime import datetime
    import json

    def get_rank_info(otaku_score: float):
        """Get rank name and level from otaku score"""
        if otaku_score < 10:
            return "캐주얼", 1
        elif otaku_score < 25:
            return "캐주얼", 2
        elif otaku_score < 50:
            return "초보", 1
        elif otaku_score < 100:
            return "초보", 2
        elif otaku_score < 150:
            return "초보", 3
        elif otaku_score < 200:
            return "입문", 1
        elif otaku_score < 250:
            return "입문", 2
        elif otaku_score < 300:
            return "입문", 3
        elif otaku_score < 400:
            return "중급", 1
        elif otaku_score < 500:
            return "중급", 2
        elif otaku_score < 600:
            return "중급", 3
        elif otaku_score < 700:
            return "마스터", 1
        elif otaku_score < 800:
            return "마스터", 2
        elif otaku_score < 900:
            return "마스터", 3
        elif otaku_score < 1000:
            return "마스터", 4
        elif otaku_score < 1100:
            return "마스터", 5
        elif otaku_score < 1300:
            return "하이마스터", 1
        elif otaku_score < 1500:
            return "하이마스터", 2
        elif otaku_score < 1700:
            return "하이마스터", 3
        elif otaku_score < 1900:
            return "하이마스터", 4
        elif otaku_score < 2100:
            return "하이마스터", 5
        elif otaku_score < 2300:
            return "하이마스터", 6
        elif otaku_score < 2600:
            return "그랜드마스터", 1
        elif otaku_score < 2900:
            return "그랜드마스터", 2
        elif otaku_score < 3200:
            return "그랜드마스터", 3
        elif otaku_score < 3500:
            return "그랜드마스터", 4
        elif otaku_score < 3800:
            return "그랜드마스터", 5
        elif otaku_score < 4100:
            return "그랜드마스터", 6
        elif otaku_score < 4400:
            return "그랜드마스터", 7
        else:
            return "레전드", 1

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

            # Get all activities for this user in chronological order
            activities = db.execute_query("""
                SELECT activity_time, activity_type
                FROM activities
                WHERE user_id = ? AND activity_type IN ('anime_rating', 'anime_review', 'character_rating', 'character_review')
                ORDER BY activity_time ASC
            """, (user_id,))

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
