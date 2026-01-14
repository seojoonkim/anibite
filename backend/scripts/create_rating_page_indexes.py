"""
Create indexes for ultra-fast rating page queries (0.1s target)
평가 페이지 초고속 쿼리를 위한 인덱스 생성
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

def create_indexes():
    """Create indexes for rating page performance"""

    indexes = [
        # ===== 애니메이션 평가 페이지 =====

        # user_ratings: (user_id, anime_id) - 가장 중요!
        """
        CREATE INDEX IF NOT EXISTS idx_user_ratings_user_anime
        ON user_ratings(user_id, anime_id)
        """,

        # user_ratings: (user_id, status, anime_id) - status 필터용
        """
        CREATE INDEX IF NOT EXISTS idx_user_ratings_user_status_anime
        ON user_ratings(user_id, status, anime_id)
        """,

        # anime: popularity DESC - 정렬용
        """
        CREATE INDEX IF NOT EXISTS idx_anime_popularity
        ON anime(popularity DESC)
        """,

        # ===== 캐릭터 평가 페이지 =====

        # anime_character: (character_id, anime_id, role) - JOIN 최적화
        """
        CREATE INDEX IF NOT EXISTS idx_anime_character_char_anime_role
        ON anime_character(character_id, anime_id, role)
        """,

        # character_ratings: (user_id, character_id) - 미평가 확인용
        """
        CREATE INDEX IF NOT EXISTS idx_character_ratings_user_char
        ON character_ratings(user_id, character_id)
        """,

        # character: favourites DESC - 정렬용
        """
        CREATE INDEX IF NOT EXISTS idx_character_favourites
        ON character(favourites DESC)
        """,

        # user_ratings: (anime_id, user_id, status) - 평가한 애니 확인
        """
        CREATE INDEX IF NOT EXISTS idx_user_ratings_anime_user_status
        ON user_ratings(anime_id, user_id, status)
        """,

        # ===== 통계 쿼리용 =====

        # user_ratings: (user_id, status) - 통계 집계
        """
        CREATE INDEX IF NOT EXISTS idx_user_ratings_user_status
        ON user_ratings(user_id, status)
        """,

        # character_ratings: (user_id, status) - 통계 집계
        """
        CREATE INDEX IF NOT EXISTS idx_character_ratings_user_status
        ON character_ratings(user_id, status)
        """,

        # ===== 리뷰 작성 페이지 =====

        # activities: (user_id, activity_type, review_content) - 리뷰 없는 항목 조회
        """
        CREATE INDEX IF NOT EXISTS idx_activities_user_type_review
        ON activities(user_id, activity_type, review_content)
        """,

        # activities: (activity_time) - 최근 평가 순 정렬용
        """
        CREATE INDEX IF NOT EXISTS idx_activities_time
        ON activities(activity_time DESC)
        """,
    ]

    print("Creating indexes for rating page performance...")

    for i, index_sql in enumerate(indexes, 1):
        try:
            db.execute_update(index_sql)
            print(f"✓ Index {i}/{len(indexes)} created successfully")
        except Exception as e:
            print(f"✗ Index {i}/{len(indexes)} failed: {e}")

    print("\n=== Index creation complete ===")
    print("Expected performance: 0.1s per query")
    print("\nTest with:")
    print("  curl http://localhost:8000/api/rating-pages/anime")
    print("  curl http://localhost:8000/api/rating-pages/characters")
    print("  curl http://localhost:8000/api/rating-pages/write-reviews")


if __name__ == "__main__":
    create_indexes()
