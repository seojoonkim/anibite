#!/usr/bin/env python3
"""
Remove Duplicate Ratings Script
중복된 애니/캐릭터 평가를 제거합니다.
같은 user_id와 item_id 조합에서 가장 최신 평가만 남기고 나머지를 삭제합니다.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import get_db

def remove_duplicate_anime_ratings():
    """중복된 애니 평가 제거"""
    db = get_db()

    print("\n" + "="*60)
    print("애니 평가 중복 확인")
    print("="*60)

    # 중복 찾기
    duplicates = db.execute_query("""
        SELECT user_id, anime_id, COUNT(*) as count
        FROM ratings
        GROUP BY user_id, anime_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    if not duplicates:
        print("✅ 중복된 애니 평가 없음")
        return 0

    print(f"⚠️  발견된 중복: {len(duplicates)}개")
    for dup in duplicates[:10]:  # Show first 10
        print(f"   User {dup[0]}, Anime {dup[1]}: {dup[2]}개 평가")

    if len(duplicates) > 10:
        print(f"   ... 외 {len(duplicates) - 10}개 더")

    # 중복 제거 (가장 최신 것만 유지)
    print("\n🗑️  중복 제거 중...")

    deleted_count = 0
    for user_id, anime_id, count in duplicates:
        # 해당 user + anime의 모든 평가를 최신순으로 가져옴
        all_ratings = db.execute_query("""
            SELECT id, rating, created_at
            FROM ratings
            WHERE user_id = ? AND anime_id = ?
            ORDER BY created_at DESC
        """, (user_id, anime_id))

        # 첫 번째(가장 최신)를 제외한 나머지 삭제
        ids_to_delete = [r[0] for r in all_ratings[1:]]

        if ids_to_delete:
            placeholders = ','.join('?' * len(ids_to_delete))
            deleted = db.execute_update(
                f"DELETE FROM ratings WHERE id IN ({placeholders})",
                tuple(ids_to_delete)
            )
            deleted_count += deleted
            print(f"   User {user_id}, Anime {anime_id}: {deleted}개 삭제 (최신 평가 유지: {all_ratings[0][1]}★)")

    print(f"\n✅ 총 {deleted_count}개 중복 평가 제거 완료")
    return deleted_count


def remove_duplicate_character_ratings():
    """중복된 캐릭터 평가 제거"""
    db = get_db()

    print("\n" + "="*60)
    print("캐릭터 평가 중복 확인")
    print("="*60)

    # 중복 찾기
    duplicates = db.execute_query("""
        SELECT user_id, character_id, COUNT(*) as count
        FROM character_ratings
        GROUP BY user_id, character_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    if not duplicates:
        print("✅ 중복된 캐릭터 평가 없음")
        return 0

    print(f"⚠️  발견된 중복: {len(duplicates)}개")
    for dup in duplicates[:10]:  # Show first 10
        print(f"   User {dup[0]}, Character {dup[1]}: {dup[2]}개 평가")

    if len(duplicates) > 10:
        print(f"   ... 외 {len(duplicates) - 10}개 더")

    # 중복 제거 (가장 최신 것만 유지)
    print("\n🗑️  중복 제거 중...")

    deleted_count = 0
    for user_id, character_id, count in duplicates:
        # 해당 user + character의 모든 평가를 최신순으로 가져옴
        all_ratings = db.execute_query("""
            SELECT id, rating, created_at
            FROM character_ratings
            WHERE user_id = ? AND character_id = ?
            ORDER BY created_at DESC
        """, (user_id, character_id))

        # 첫 번째(가장 최신)를 제외한 나머지 삭제
        ids_to_delete = [r[0] for r in all_ratings[1:]]

        if ids_to_delete:
            placeholders = ','.join('?' * len(ids_to_delete))
            deleted = db.execute_update(
                f"DELETE FROM character_ratings WHERE id IN ({placeholders})",
                tuple(ids_to_delete)
            )
            deleted_count += deleted
            print(f"   User {user_id}, Character {character_id}: {deleted}개 삭제 (최신 평가 유지: {all_ratings[0][1]}★)")

    print(f"\n✅ 총 {deleted_count}개 중복 평가 제거 완료")
    return deleted_count


def main():
    print("\n" + "="*60)
    print("중복 평가 제거 스크립트")
    print("="*60)

    # 애니 평가 중복 제거
    anime_deleted = remove_duplicate_anime_ratings()

    # 캐릭터 평가 중복 제거
    character_deleted = remove_duplicate_character_ratings()

    # 최종 결과
    print("\n" + "="*60)
    print("완료!")
    print("="*60)
    print(f"애니 평가 중복 제거: {anime_deleted}개")
    print(f"캐릭터 평가 중복 제거: {character_deleted}개")
    print(f"총 제거: {anime_deleted + character_deleted}개")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
