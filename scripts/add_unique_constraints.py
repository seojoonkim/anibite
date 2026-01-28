#!/usr/bin/env python3
"""
Add UNIQUE Constraints Script
평가 테이블에 UNIQUE 제약 조건을 추가하여 중복을 방지합니다.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import get_db

def add_unique_constraints():
    """UNIQUE 제약 조건 추가"""
    db = get_db()

    print("\n" + "="*60)
    print("UNIQUE 제약 조건 추가")
    print("="*60)

    try:
        # 1. ratings 테이블에 UNIQUE INDEX 추가
        print("\n1. ratings 테이블 (애니 평가)")
        print("   UNIQUE INDEX 추가: (user_id, anime_id)")

        # 기존 인덱스 확인
        existing_indexes = db.execute_query("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='ratings' AND name='idx_ratings_user_anime_unique'
        """)

        if existing_indexes:
            print("   ⚠️  인덱스가 이미 존재합니다. 삭제 후 재생성...")
            db.execute_update("DROP INDEX idx_ratings_user_anime_unique")

        db.execute_update("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ratings_user_anime_unique
            ON ratings(user_id, anime_id)
        """)
        print("   ✅ UNIQUE INDEX 생성 완료")

        # 2. character_ratings 테이블에 UNIQUE INDEX 추가
        print("\n2. character_ratings 테이블 (캐릭터 평가)")
        print("   UNIQUE INDEX 추가: (user_id, character_id)")

        # 기존 인덱스 확인
        existing_indexes = db.execute_query("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='character_ratings' AND name='idx_character_ratings_user_character_unique'
        """)

        if existing_indexes:
            print("   ⚠️  인덱스가 이미 존재합니다. 삭제 후 재생성...")
            db.execute_update("DROP INDEX idx_character_ratings_user_character_unique")

        db.execute_update("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_character_ratings_user_character_unique
            ON character_ratings(user_id, character_id)
        """)
        print("   ✅ UNIQUE INDEX 생성 완료")

        print("\n" + "="*60)
        print("✅ 모든 제약 조건 추가 완료!")
        print("="*60)
        print("앞으로 같은 사용자가 같은 애니/캐릭터에")
        print("중복 평가를 하려고 하면 자동으로 차단됩니다.")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_constraints():
    """제약 조건이 제대로 적용되었는지 확인"""
    db = get_db()

    print("\n" + "="*60)
    print("제약 조건 확인")
    print("="*60)

    # ratings 인덱스 확인
    indexes = db.execute_query("""
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND tbl_name='ratings' AND name LIKE '%unique%'
    """)

    print("\n1. ratings 테이블 UNIQUE 인덱스:")
    if indexes:
        for idx in indexes:
            print(f"   ✅ {idx[0]}")
    else:
        print("   ⚠️  UNIQUE 인덱스 없음")

    # character_ratings 인덱스 확인
    indexes = db.execute_query("""
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND tbl_name='character_ratings' AND name LIKE '%unique%'
    """)

    print("\n2. character_ratings 테이블 UNIQUE 인덱스:")
    if indexes:
        for idx in indexes:
            print(f"   ✅ {idx[0]}")
    else:
        print("   ⚠️  UNIQUE 인덱스 없음")

    print("\n" + "="*60 + "\n")


def main():
    add_unique_constraints()
    verify_constraints()


if __name__ == "__main__":
    main()
