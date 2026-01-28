#!/usr/bin/env python3
"""
Ensure UNIQUE Constraints
서버 startup 시 UNIQUE 제약 조건이 존재하는지 확인하고 추가합니다.
"""
from database import get_db

def ensure_unique_constraints():
    """UNIQUE 제약 조건 확인 및 추가"""
    db = get_db()

    try:
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


if __name__ == "__main__":
    ensure_unique_constraints()
