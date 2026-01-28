#!/usr/bin/env python3
"""
Clean Production Duplicates
프로덕션 DB에서 중복 데이터를 즉시 제거합니다.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import get_db

def clean_duplicates():
    """중복 데이터 제거"""
    db = get_db()

    print("="*60)
    print("프로덕션 중복 데이터 제거")
    print("="*60)

    # 1. character_ratings 중복 제거
    print("\n1️⃣ 캐릭터 평가 중복 확인...")
    duplicates = db.execute_query("""
        SELECT user_id, character_id, COUNT(*) as count
        FROM character_ratings
        GROUP BY user_id, character_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"   ⚠️  {len(duplicates)}개 중복 발견!")
        total_deleted = 0
        for user_id, character_id, count in duplicates:
            # 최신 것만 유지
            all_ratings = db.execute_query("""
                SELECT id, rating, created_at, updated_at
                FROM character_ratings
                WHERE user_id = ? AND character_id = ?
                ORDER BY updated_at DESC, created_at DESC
            """, (user_id, character_id))

            print(f"\n   User {user_id}, Character {character_id}:")
            print(f"      총 {len(all_ratings)}개 → 1개로 정리")
            for i, rating in enumerate(all_ratings):
                if i == 0:
                    print(f"      ✅ KEEP: rating={rating[1]}, updated={rating[3]}")
                else:
                    print(f"      ❌ DELETE: rating={rating[1]}, updated={rating[3]}")

            # 첫 번째 제외한 나머지 삭제
            ids_to_delete = [r[0] for r in all_ratings[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                deleted = db.execute_update(
                    f"DELETE FROM character_ratings WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
                total_deleted += deleted

        print(f"\n   ✅ 총 {total_deleted}개 중복 캐릭터 평가 제거 완료")
    else:
        print("   ✅ 중복 없음")

    # 2. user_ratings 중복 제거
    print("\n2️⃣ 애니 평가 중복 확인...")
    duplicates = db.execute_query("""
        SELECT user_id, anime_id, COUNT(*) as count
        FROM user_ratings
        GROUP BY user_id, anime_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"   ⚠️  {len(duplicates)}개 중복 발견!")
        total_deleted = 0
        for user_id, anime_id, count in duplicates:
            all_ratings = db.execute_query("""
                SELECT id, rating, created_at, updated_at
                FROM user_ratings
                WHERE user_id = ? AND anime_id = ?
                ORDER BY updated_at DESC, created_at DESC
            """, (user_id, anime_id))

            print(f"\n   User {user_id}, Anime {anime_id}:")
            print(f"      총 {len(all_ratings)}개 → 1개로 정리")

            ids_to_delete = [r[0] for r in all_ratings[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                deleted = db.execute_update(
                    f"DELETE FROM user_ratings WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
                total_deleted += deleted

        print(f"\n   ✅ 총 {total_deleted}개 중복 애니 평가 제거 완료")
    else:
        print("   ✅ 중복 없음")

    # 3. activities 중복 제거 (character_rating)
    print("\n3️⃣ 캐릭터 활동 중복 확인...")
    duplicates = db.execute_query("""
        SELECT user_id, item_id, COUNT(*) as count
        FROM activities
        WHERE activity_type = 'character_rating'
        GROUP BY user_id, item_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"   ⚠️  {len(duplicates)}개 중복 발견!")
        total_deleted = 0
        for user_id, item_id, count in duplicates:
            all_activities = db.execute_query("""
                SELECT id, activity_time
                FROM activities
                WHERE activity_type = 'character_rating'
                  AND user_id = ? AND item_id = ?
                ORDER BY activity_time DESC, created_at DESC
            """, (user_id, item_id))

            print(f"\n   User {user_id}, Character {item_id}:")
            print(f"      총 {len(all_activities)}개 → 1개로 정리")

            ids_to_delete = [r[0] for r in all_activities[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                deleted = db.execute_update(
                    f"DELETE FROM activities WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
                total_deleted += deleted

        print(f"\n   ✅ 총 {total_deleted}개 중복 캐릭터 활동 제거 완료")
    else:
        print("   ✅ 중복 없음")

    # 4. activities 중복 제거 (anime_rating)
    print("\n4️⃣ 애니 활동 중복 확인...")
    duplicates = db.execute_query("""
        SELECT user_id, item_id, COUNT(*) as count
        FROM activities
        WHERE activity_type = 'anime_rating'
        GROUP BY user_id, item_id
        HAVING COUNT(*) > 1
    """)

    if duplicates:
        print(f"   ⚠️  {len(duplicates)}개 중복 발견!")
        total_deleted = 0
        for user_id, item_id, count in duplicates:
            all_activities = db.execute_query("""
                SELECT id, activity_time
                FROM activities
                WHERE activity_type = 'anime_rating'
                  AND user_id = ? AND item_id = ?
                ORDER BY activity_time DESC, created_at DESC
            """, (user_id, item_id))

            ids_to_delete = [r[0] for r in all_activities[1:]]
            if ids_to_delete:
                placeholders = ','.join('?' * len(ids_to_delete))
                deleted = db.execute_update(
                    f"DELETE FROM activities WHERE id IN ({placeholders})",
                    tuple(ids_to_delete)
                )
                total_deleted += deleted

        print(f"\n   ✅ 총 {total_deleted}개 중복 애니 활동 제거 완료")
    else:
        print("   ✅ 중복 없음")

    print("\n" + "="*60)
    print("✅ 중복 제거 완료!")
    print("="*60)


if __name__ == "__main__":
    clean_duplicates()
