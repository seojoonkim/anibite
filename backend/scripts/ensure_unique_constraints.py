#!/usr/bin/env python3
"""
Ensure UNIQUE Constraints
서버 startup 시 UNIQUE 제약 조건이 존재하는지 확인하고 추가합니다.
중복 데이터가 있으면 제거합니다.
"""
from database import get_db

def remove_duplicates():
    """중복 데이터 제거"""
    db = get_db()

    # 1. user_ratings 중복 제거
    duplicates = db.execute_query("""
        SELECT user_id, anime_id, COUNT(*) as count
        FROM user_ratings
        GROUP BY user_id, anime_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"[Startup] Found {len(duplicates)} duplicate anime ratings, removing...")
        for user_id, anime_id, count in duplicates:
            # 최신 것만 유지
            all_ratings = db.execute_query("""
                SELECT id FROM user_ratings
                WHERE user_id = ? AND anime_id = ?
                ORDER BY updated_at DESC, created_at DESC
            """, (user_id, anime_id))

            # 첫 번째 제외한 나머지 삭제
            ids_to_delete = [r[0] for r in all_ratings[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                db.execute_update(
                    f"DELETE FROM user_ratings WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
        print(f"[Startup] Removed duplicate anime ratings")

    # 2. character_ratings 중복 제거
    duplicates = db.execute_query("""
        SELECT user_id, character_id, COUNT(*) as count
        FROM character_ratings
        GROUP BY user_id, character_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"[Startup] Found {len(duplicates)} duplicate character ratings, removing...")
        for user_id, character_id, count in duplicates:
            # 최신 것만 유지
            all_ratings = db.execute_query("""
                SELECT id FROM character_ratings
                WHERE user_id = ? AND character_id = ?
                ORDER BY updated_at DESC, created_at DESC
            """, (user_id, character_id))

            # 첫 번째 제외한 나머지 삭제
            ids_to_delete = [r[0] for r in all_ratings[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                db.execute_update(
                    f"DELETE FROM character_ratings WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
        print(f"[Startup] Removed duplicate character ratings")

    # 3. activities 테이블에서도 중복 제거
    # character_rating 활동 중복 제거
    char_dup_activities = db.execute_query("""
        SELECT user_id, item_id, COUNT(*) as count
        FROM activities
        WHERE activity_type = 'character_rating'
        GROUP BY user_id, item_id
        HAVING COUNT(*) > 1
    """)

    if char_dup_activities:
        print(f"[Startup] Found {len(char_dup_activities)} duplicate character rating activities, removing...")
        for user_id, item_id, count in char_dup_activities:
            # 최신 것만 유지
            all_activities = db.execute_query("""
                SELECT id FROM activities
                WHERE activity_type = 'character_rating'
                  AND user_id = ? AND item_id = ?
                ORDER BY activity_time DESC, created_at DESC
            """, (user_id, item_id))

            ids_to_delete = [r[0] for r in all_activities[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                db.execute_update(
                    f"DELETE FROM activities WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
        print(f"[Startup] Removed duplicate character rating activities")

    # anime_rating 활동 중복 제거
    anime_dup_activities = db.execute_query("""
        SELECT user_id, item_id, COUNT(*) as count
        FROM activities
        WHERE activity_type = 'anime_rating'
        GROUP BY user_id, item_id
        HAVING COUNT(*) > 1
    """)

    if anime_dup_activities:
        print(f"[Startup] Found {len(anime_dup_activities)} duplicate anime rating activities, removing...")
        for user_id, item_id, count in anime_dup_activities:
            all_activities = db.execute_query("""
                SELECT id FROM activities
                WHERE activity_type = 'anime_rating'
                  AND user_id = ? AND item_id = ?
                ORDER BY activity_time DESC, created_at DESC
            """, (user_id, item_id))

            ids_to_delete = [r[0] for r in all_activities[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                db.execute_update(
                    f"DELETE FROM activities WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
        print(f"[Startup] Removed duplicate anime rating activities")


def ensure_unique_constraints():
    """UNIQUE 제약 조건 확인 및 추가"""
    db = get_db()

    try:
        # 0. 먼저 중복 데이터 제거
        print("[Startup] Checking for duplicate ratings...")
        remove_duplicates()

        # 1. user_ratings 테이블에 UNIQUE INDEX
        db.execute_update("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_ratings_user_anime_unique
            ON user_ratings(user_id, anime_id)
        """)

        # 2. character_ratings 테이블에 UNIQUE INDEX
        db.execute_update("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_character_ratings_user_character_unique
            ON character_ratings(user_id, character_id)
        """)

        # 3. 레거시 ratings 테이블 제거 (존재하는 경우)
        tables = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ratings'"
        )
        if tables:
            db.execute_update("DROP TABLE ratings")
            print("[Startup] Removed legacy 'ratings' table")

        print("[Startup] UNIQUE constraints ensured")

    except Exception as e:
        print(f"[Startup] Warning: Failed to ensure UNIQUE constraints: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    ensure_unique_constraints()
