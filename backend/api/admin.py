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


@router.get("/debug-user-feed/{user_id}")
def debug_user_feed(user_id: int, limit: int = 50):
    """Debug user feed data - check what's being returned"""
    try:
        from services.feed_service import get_user_feed

        # Check activities table directly
        activities_in_db = db.execute_query("""
            SELECT activity_type, activity_time
            FROM activities
            WHERE user_id = ?
            ORDER BY activity_time DESC
            LIMIT 20
        """, (user_id,))

        # Get feed
        feed_data = get_user_feed(user_id, current_user_id=user_id, limit=limit, offset=0)

        # Count activity types
        activity_types = {}
        rank_promotions = []

        for activity in feed_data:
            act_type = activity.get('activity_type')
            activity_types[act_type] = activity_types.get(act_type, 0) + 1

            if act_type == 'rank_promotion':
                rank_promotions.append({
                    'activity_time': activity.get('activity_time'),
                    'metadata': activity.get('metadata'),
                    'has_metadata': activity.get('metadata') is not None
                })

        return {
            "user_id": user_id,
            "total_activities_from_feed": len(feed_data),
            "activity_types_from_feed": activity_types,
            "rank_promotions_from_feed": rank_promotions,
            "recent_20_from_db": [{"type": row[0], "time": row[1]} for row in activities_in_db],
            "first_activity": feed_data[0] if feed_data else None
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{traceback.format_exc()}")


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


@router.post("/fix-korean-names")
def fix_korean_names_endpoint():
    """
    Fix character Korean names in activities table
    캐릭터 한국어 이름 수정 (name_native → name_korean)
    """
    try:
        # Step 1: Check current data
        sample_before = db.execute_query("""
            SELECT item_title, item_title_korean
            FROM activities
            WHERE activity_type = 'character_rating'
            LIMIT 3
        """)

        before_data = [{"title": row[0], "korean": row[1]} for row in sample_before] if sample_before else []

        # Step 2: Drop old triggers
        triggers_to_drop = [
            'trg_character_rating_insert',
            'trg_character_rating_update',
            'trg_character_rating_delete',
            'trg_character_review_insert'
        ]

        for trigger_name in triggers_to_drop:
            try:
                db.execute_query(f"DROP TRIGGER IF EXISTS {trigger_name}")
            except Exception as e:
                pass  # Ignore errors

        # Step 3: Update existing data
        update_query = """
        UPDATE activities
        SET item_title_korean = (
            SELECT c.name_korean
            FROM character c
            WHERE c.id = activities.item_id
        )
        WHERE activity_type IN ('character_rating', 'character_review')
        AND item_id IS NOT NULL
        """

        db.execute_query(update_query)

        # Step 4: Recreate triggers
        # Character rating insert trigger
        db.execute_query("""
            CREATE TRIGGER IF NOT EXISTS trg_character_rating_insert
            AFTER INSERT ON character_ratings
            WHEN NEW.rating IS NOT NULL
            BEGIN
                DELETE FROM activities
                WHERE activity_type = 'character_rating'
                  AND user_id = NEW.user_id
                  AND item_id = NEW.character_id;

                INSERT INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    item_title, item_title_korean, item_image,
                    rating, review_id, review_content,
                    anime_id, anime_title, anime_title_korean
                )
                SELECT
                    'character_rating',
                    NEW.user_id,
                    NEW.character_id,
                    COALESCE(rev.created_at, NEW.updated_at),
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0),
                    c.name_full,
                    c.name_korean,
                    COALESCE('/' || c.image_local, c.image_url),
                    NEW.rating,
                    rev.id,
                    rev.content,
                    (SELECT a.id FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                    (SELECT a.title_romaji FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                    (SELECT a.title_korean FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
                FROM users u
                JOIN character c ON c.id = NEW.character_id
                LEFT JOIN user_stats us ON u.id = NEW.user_id
                LEFT JOIN character_reviews rev ON rev.user_id = NEW.user_id AND rev.character_id = NEW.character_id
                WHERE u.id = NEW.user_id;
            END
        """)

        # Character rating update trigger
        db.execute_query("""
            CREATE TRIGGER IF NOT EXISTS trg_character_rating_update
            AFTER UPDATE ON character_ratings
            WHEN NEW.rating IS NOT NULL
            BEGIN
                DELETE FROM activities
                WHERE activity_type = 'character_rating'
                  AND user_id = NEW.user_id
                  AND item_id = NEW.character_id;

                INSERT INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    item_title, item_title_korean, item_image,
                    rating, review_id, review_content,
                    anime_id, anime_title, anime_title_korean
                )
                SELECT
                    'character_rating',
                    NEW.user_id,
                    NEW.character_id,
                    COALESCE(rev.created_at, NEW.updated_at),
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0),
                    c.name_full,
                    c.name_korean,
                    COALESCE('/' || c.image_local, c.image_url),
                    NEW.rating,
                    rev.id,
                    rev.content,
                    (SELECT a.id FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                    (SELECT a.title_romaji FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                    (SELECT a.title_korean FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
                FROM users u
                JOIN character c ON c.id = NEW.character_id
                LEFT JOIN user_stats us ON u.id = NEW.user_id
                LEFT JOIN character_reviews rev ON rev.user_id = NEW.user_id AND rev.character_id = NEW.character_id
                WHERE u.id = NEW.user_id;
            END
        """)

        # Character rating delete trigger
        db.execute_query("""
            CREATE TRIGGER IF NOT EXISTS trg_character_rating_delete
            AFTER DELETE ON character_ratings
            BEGIN
                DELETE FROM activities
                WHERE activity_type = 'character_rating'
                  AND user_id = OLD.user_id
                  AND item_id = OLD.character_id;
            END
        """)

        # Character review insert trigger
        db.execute_query("""
            CREATE TRIGGER IF NOT EXISTS trg_character_review_insert
            AFTER INSERT ON character_reviews
            BEGIN
                UPDATE activities
                SET review_id = NEW.id,
                    review_content = NEW.content,
                    activity_time = NEW.created_at
                WHERE activity_type = 'character_rating'
                  AND user_id = NEW.user_id
                  AND item_id = NEW.character_id;

                INSERT INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    item_title, item_title_korean, item_image,
                    review_id, review_content,
                    anime_title, anime_title_korean
                )
                SELECT
                    'character_review',
                    NEW.user_id,
                    NEW.character_id,
                    NEW.created_at,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0),
                    c.name_full,
                    c.name_korean,
                    COALESCE('/' || c.image_local, c.image_url),
                    NEW.id,
                    NEW.content,
                    (SELECT a.title_romaji FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1),
                    (SELECT a.title_korean FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = NEW.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1)
                FROM users u
                JOIN character c ON c.id = NEW.character_id
                LEFT JOIN user_stats us ON u.id = NEW.user_id
                WHERE u.id = NEW.user_id
                  AND NOT EXISTS (
                      SELECT 1 FROM character_ratings cr
                      WHERE cr.user_id = NEW.user_id
                        AND cr.character_id = NEW.character_id
                        AND cr.rating IS NOT NULL
                  );
            END
        """)

        # Step 5: Verify changes
        sample_after = db.execute_query("""
            SELECT item_title, item_title_korean
            FROM activities
            WHERE activity_type = 'character_rating'
            LIMIT 5
        """)

        after_data = [{"title": row[0], "korean": row[1]} for row in sample_after] if sample_after else []

        # Count total
        count = db.execute_query("""
            SELECT COUNT(*)
            FROM activities
            WHERE activity_type IN ('character_rating', 'character_review')
            AND item_title_korean IS NOT NULL
        """, fetch_one=True)

        total_updated = count[0] if count else 0

        return {
            "success": True,
            "message": "Korean character names fixed successfully",
            "before_sample": before_data,
            "after_sample": after_data,
            "total_updated": total_updated,
            "triggers_recreated": 4
        }

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{traceback.format_exc()}")


@router.post("/create-notifications-table")
def create_notifications_table():
    """
    Create notifications table if it doesn't exist
    알림 테이블 생성
    """
    try:
        # Check if table exists
        existing = db.execute_query("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='notifications'
        """)

        if existing:
            return {
                "success": True,
                "message": "Notifications table already exists",
                "created": False
            }

        # Create notifications table
        db.execute_query("""
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                actor_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                activity_id INTEGER,
                comment_id INTEGER,
                content TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better performance
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user
            ON notifications(user_id, created_at DESC)
        """)

        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_notifications_read
            ON notifications(user_id, is_read)
        """)

        # Verify table was created
        verify = db.execute_query("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='notifications'
        """)

        return {
            "success": True,
            "message": "Notifications table created successfully",
            "created": True,
            "verified": bool(verify)
        }

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{traceback.format_exc()}")


@router.post("/rebuild-activities")
def rebuild_activities_endpoint():
    """
    Rebuild activities table from user_ratings and character_ratings
    이 API는 activities 테이블을 완전히 재구축합니다
    """
    try:

        # 1. 애니 평가 마이그레이션
        print("Migrating anime ratings...")
        count_anime = db.execute_query("""
            SELECT COUNT(*) as count
            FROM user_ratings ur
            WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
        """, fetch_one=True)

        total_anime = count_anime['count'] if count_anime else 0
        print(f"  Found {total_anime} anime ratings to migrate")

        if total_anime > 0:
            db.execute_query("""
                INSERT OR REPLACE INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    item_title, item_title_korean, item_image,
                    rating, review_title, review_content, is_spoiler
                )
                SELECT
                    'anime_rating' as activity_type,
                    ur.user_id,
                    ur.anime_id as item_id,
                    COALESCE(rev.created_at, ur.updated_at) as activity_time,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score,
                    a.title_romaji as item_title,
                    a.title_korean as item_title_korean,
                    COALESCE('/' || a.cover_image_local, a.cover_image_url) as item_image,
                    ur.rating,
                    rev.title as review_title,
                    rev.content as review_content,
                    COALESCE(rev.is_spoiler, 0) as is_spoiler
                FROM user_ratings ur
                JOIN users u ON ur.user_id = u.id
                JOIN anime a ON ur.anime_id = a.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                LEFT JOIN user_reviews rev ON rev.user_id = ur.user_id AND rev.anime_id = ur.anime_id
                WHERE ur.status = 'RATED' AND ur.rating IS NOT NULL
            """)

        # 2. 캐릭터 평가 마이그레이션
        print("Migrating character ratings...")
        count_char = db.execute_query("""
            SELECT COUNT(*) as count
            FROM character_ratings cr
            WHERE cr.rating IS NOT NULL
        """, fetch_one=True)

        total_char = count_char['count'] if count_char else 0
        print(f"  Found {total_char} character ratings to migrate")

        if total_char > 0:
            db.execute_query("""
                INSERT OR REPLACE INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    item_title, item_title_korean, item_image,
                    rating, review_title, review_content, is_spoiler,
                    anime_id, anime_title, anime_title_korean
                )
                SELECT
                    'character_rating' as activity_type,
                    cr.user_id,
                    cr.character_id as item_id,
                    COALESCE(rev.created_at, cr.updated_at) as activity_time,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score,
                    c.name_full as item_title,
                    c.name_korean as item_title_korean,
                    COALESCE('/' || c.image_local, c.image_url) as item_image,
                    cr.rating,
                    rev.title as review_title,
                    rev.content as review_content,
                    COALESCE(rev.is_spoiler, 0) as is_spoiler,
                    (SELECT a.id FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = cr.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_id,
                    (SELECT a.title_romaji FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = cr.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title,
                    (SELECT a.title_korean FROM anime a
                     JOIN anime_character ac ON a.id = ac.anime_id
                     WHERE ac.character_id = cr.character_id
                     ORDER BY CASE WHEN ac.role = 'MAIN' THEN 0 ELSE 1 END LIMIT 1) as anime_title_korean
                FROM character_ratings cr
                JOIN users u ON cr.user_id = u.id
                JOIN character c ON cr.character_id = c.id
                LEFT JOIN user_stats us ON u.id = us.user_id
                LEFT JOIN character_reviews rev ON rev.user_id = cr.user_id AND rev.character_id = cr.character_id
                WHERE cr.rating IS NOT NULL
            """)

        # 3. 유저 포스트 마이그레이션
        print("Migrating user posts...")
        count_posts = db.execute_query("""
            SELECT COUNT(*) as count FROM user_posts
        """, fetch_one=True)

        total_posts = count_posts['count'] if count_posts else 0
        print(f"  Found {total_posts} user posts to migrate")

        if total_posts > 0:
            db.execute_query("""
                INSERT OR REPLACE INTO activities (
                    activity_type, user_id, item_id, activity_time,
                    username, display_name, avatar_url, otaku_score,
                    review_content
                )
                SELECT
                    'user_post' as activity_type,
                    up.user_id,
                    up.id as item_id,
                    up.created_at as activity_time,
                    u.username,
                    u.display_name,
                    u.avatar_url,
                    COALESCE(us.otaku_score, 0) as otaku_score,
                    up.content as review_content
                FROM user_posts up
                JOIN users u ON up.user_id = u.id
                LEFT JOIN user_stats us ON u.id = us.user_id
            """)

        return {
            "success": True,
            "anime_ratings_migrated": total_anime,
            "character_ratings_migrated": total_char,
            "user_posts_migrated": total_posts,
            "total_migrated": total_anime + total_char + total_posts
        }

    except Exception as e:
        print(f"Error rebuilding activities: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
