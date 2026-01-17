#!/usr/bin/env python3
"""
로컬 DB에서 한국어 이름 UPDATE SQL 문 생성
이 SQL을 Railway에서 실행하면 됨
"""
import sys
import os
from pathlib import Path

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# SQL 파일 경로
OUTPUT_SQL = Path(__file__).parent / "korean_names_update.sql"


def generate_update_sql():
    """로컬 DB에서 한국어 이름 UPDATE SQL 생성"""
    print("\n📋 로컬 DB에서 한국어 이름 추출 중...")

    query = """
        SELECT id, name_korean
        FROM character
        WHERE name_korean IS NOT NULL
          AND name_korean != ''
          AND LENGTH(name_korean) >= 2
        ORDER BY id
    """

    characters = db.execute_query(query)

    if not characters:
        print("❌ 한국어 이름이 있는 캐릭터를 찾을 수 없습니다.")
        return None

    print(f"✅ 총 {len(characters)}개 캐릭터의 한국어 이름을 추출했습니다.")

    # Generate SQL
    sql_lines = [
        "-- AniPass 캐릭터 한국어 이름 업데이트 SQL",
        f"-- 총 {len(characters)}개 캐릭터",
        "-- 생성일: " + str(Path(__file__).stat().st_mtime),
        "",
        "BEGIN TRANSACTION;",
        ""
    ]

    for char in characters:
        char_id = char['id'] if isinstance(char, dict) else char[0]
        name_korean = char['name_korean'] if isinstance(char, dict) else char[1]

        # Escape single quotes
        name_korean_escaped = name_korean.replace("'", "''")

        sql_lines.append(f"UPDATE character SET name_korean = '{name_korean_escaped}' WHERE id = {char_id};")

    sql_lines.extend([
        "",
        "-- activities 테이블도 업데이트",
        "UPDATE activities",
        "SET item_title_korean = (",
        "    SELECT c.name_korean",
        "    FROM character c",
        "    WHERE c.id = activities.item_id",
        ")",
        "WHERE activity_type IN ('character_rating', 'character_review')",
        "AND item_id IS NOT NULL;",
        "",
        "COMMIT;",
        ""
    ])

    # Save to file
    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"\n💾 SQL 파일 저장됨: {OUTPUT_SQL}")
    print(f"   파일 크기: {OUTPUT_SQL.stat().st_size / 1024:.1f} KB")
    print(f"   UPDATE 문 개수: {len(characters)}개")

    return OUTPUT_SQL


def main():
    print("="*60)
    print("🚀 한국어 이름 UPDATE SQL 생성")
    print("="*60)

    sql_file = generate_update_sql()
    if not sql_file:
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ SQL 생성 완료!")
    print(f"\n다음 단계:")
    print(f"1. {sql_file} 파일 확인")
    print(f"2. Railway에서 실행:")
    print(f"   railway run sqlite3 /app/data/anime.db < {sql_file.name}")
    print(f"   또는 Railway shell에서 직접 실행")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
