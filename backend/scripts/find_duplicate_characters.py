"""
중복 캐릭터 찾기 및 평가 정리
같은 캐릭터가 다른 애니메이션에서 다른 ID로 등록된 경우를 찾아서 정리
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


def find_duplicate_characters():
    """같은 이름의 중복 캐릭터 찾기"""
    print("=" * 60)
    print("Finding duplicate characters by Korean name...")
    print("=" * 60)

    # 한글 이름이 같은 캐릭터들 찾기
    query = """
    SELECT
        c1.id as id1, c1.name_full as name1, c1.name_korean,
        c2.id as id2, c2.name_full as name2,
        GROUP_CONCAT(DISTINCT a1.title_korean || ' (' || a1.id || ')') as anime1,
        GROUP_CONCAT(DISTINCT a2.title_korean || ' (' || a2.id || ')') as anime2
    FROM character c1
    JOIN character c2 ON c1.name_korean = c2.name_korean AND c1.id < c2.id
    LEFT JOIN anime_character ac1 ON ac1.character_id = c1.id
    LEFT JOIN anime a1 ON ac1.anime_id = a1.id
    LEFT JOIN anime_character ac2 ON ac2.character_id = c2.id
    LEFT JOIN anime a2 ON ac2.anime_id = a2.id
    WHERE c1.name_korean IS NOT NULL AND c1.name_korean != ''
    GROUP BY c1.id, c2.id
    ORDER BY c1.name_korean
    """

    duplicates = db.execute_query(query)

    if not duplicates:
        print("No duplicate characters found!")
        return []

    print(f"\nFound {len(duplicates)} potential duplicate pairs:\n")

    for dup in duplicates:
        print(f"  [{dup['name_korean']}]")
        print(f"    ID {dup['id1']}: {dup['name1']}")
        print(f"      Anime: {dup['anime1']}")
        print(f"    ID {dup['id2']}: {dup['name2']}")
        print(f"      Anime: {dup['anime2']}")
        print()

    return duplicates


def find_users_with_duplicate_ratings(duplicates):
    """중복 캐릭터에 대해 여러 번 평가한 사용자 찾기"""
    print("=" * 60)
    print("Finding users who rated duplicate characters...")
    print("=" * 60)

    affected_users = []

    for dup in duplicates:
        id1, id2 = dup['id1'], dup['id2']

        query = """
        SELECT
            u.id as user_id, u.username,
            cr1.rating as rating1, cr1.id as rating_id1,
            cr2.rating as rating2, cr2.id as rating_id2,
            ? as char_id1, ? as char_id2, ? as char_name
        FROM character_ratings cr1
        JOIN character_ratings cr2 ON cr1.user_id = cr2.user_id
        JOIN users u ON cr1.user_id = u.id
        WHERE cr1.character_id = ? AND cr2.character_id = ?
        """

        users = db.execute_query(query, (id1, id2, dup['name_korean'], id1, id2))

        if users:
            for user in users:
                affected_users.append(user)
                print(f"\n  User: {user['username']} (ID: {user['user_id']})")
                print(f"    Character: {user['char_name']}")
                print(f"    Rating for ID {user['char_id1']}: {user['rating1']} (rating_id: {user['rating_id1']})")
                print(f"    Rating for ID {user['char_id2']}: {user['rating2']} (rating_id: {user['rating_id2']})")

    if not affected_users:
        print("\nNo users found with duplicate ratings!")
    else:
        print(f"\nTotal affected: {len(affected_users)} duplicate rating pairs")

    return affected_users


def cleanup_duplicate_ratings(affected_users, dry_run=True):
    """중복 평가 정리 - 더 낮은 character_id를 canonical로 유지"""
    print("\n" + "=" * 60)
    print(f"Cleaning up duplicate ratings... (dry_run={dry_run})")
    print("=" * 60)

    for user in affected_users:
        # 더 낮은 character_id를 canonical로 사용
        canonical_id = min(user['char_id1'], user['char_id2'])
        remove_id = max(user['char_id1'], user['char_id2'])

        # 더 높은 평점을 유지
        if user['rating1'] is None:
            keep_rating = user['rating2']
        elif user['rating2'] is None:
            keep_rating = user['rating1']
        else:
            keep_rating = max(user['rating1'], user['rating2'])

        print(f"\n  User {user['username']}: {user['char_name']}")
        print(f"    Keep: character_id={canonical_id}, rating={keep_rating}")
        print(f"    Remove: character_id={remove_id}")

        if not dry_run:
            # canonical 평점 업데이트
            if keep_rating:
                db.execute_update(
                    "UPDATE character_ratings SET rating = ? WHERE user_id = ? AND character_id = ?",
                    (keep_rating, user['user_id'], canonical_id)
                )

            # 중복 평점 삭제
            db.execute_update(
                "DELETE FROM character_ratings WHERE user_id = ? AND character_id = ?",
                (user['user_id'], remove_id)
            )

            # activities 테이블에서도 정리
            db.execute_update(
                "DELETE FROM activities WHERE user_id = ? AND activity_type = 'character_rating' AND item_id = ?",
                (user['user_id'], remove_id)
            )

            print(f"    ✓ Cleaned up!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix', action='store_true', help='Actually fix the duplicates (default: dry run)')
    args = parser.parse_args()

    duplicates = find_duplicate_characters()

    if duplicates:
        affected = find_users_with_duplicate_ratings(duplicates)

        if affected:
            cleanup_duplicate_ratings(affected, dry_run=not args.fix)

            if not args.fix:
                print("\n" + "=" * 60)
                print("This was a DRY RUN. No changes were made.")
                print("Run with --fix flag to actually clean up duplicates.")
                print("=" * 60)
