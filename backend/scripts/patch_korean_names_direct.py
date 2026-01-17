#!/usr/bin/env python3
"""
Direct DB script to patch Korean character names
Railway에서 실행 가능한 standalone 스크립트
"""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from config import DATABASE_PATH

# JSON 파일 경로 (로컬에서 생성한 데이터)
KOREAN_NAMES_JSON = Path(__file__).parent / "korean_names_patch.json"


def load_korean_names():
    """Load Korean names from JSON file"""
    if not KOREAN_NAMES_JSON.exists():
        print(f"❌ JSON 파일을 찾을 수 없습니다: {KOREAN_NAMES_JSON}")
        print(f"   먼저 로컬에서 export_korean_names_json.py를 실행하세요")
        return None

    with open(KOREAN_NAMES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def patch_korean_names(names_dict):
    """Patch Korean names directly to database"""
    print(f"\n📊 총 {len(names_dict)}개 캐릭터를 패치합니다.")
    print(f"📍 Database: {DATABASE_PATH}")

    updated = 0
    failed = []

    for char_id, korean_name in names_dict.items():
        try:
            result = db.execute_update(
                "UPDATE character SET name_korean = ? WHERE id = ?",
                (korean_name, int(char_id))
            )
            if result > 0:
                updated += 1
                if updated % 1000 == 0:
                    print(f"  진행중: {updated}/{len(names_dict)}")
        except Exception as e:
            failed.append({"id": char_id, "error": str(e)})

    # Also update activities table
    print("\n📝 activities 테이블 업데이트 중...")
    db.execute_update("""
        UPDATE activities
        SET item_title_korean = (
            SELECT c.name_korean
            FROM character c
            WHERE c.id = activities.item_id
        )
        WHERE activity_type IN ('character_rating', 'character_review')
        AND item_id IS NOT NULL
    """)

    print(f"\n{'='*60}")
    print(f"✅ 패치 완료!")
    print(f"  성공: {updated}개")
    print(f"  실패: {len(failed)}개")
    if failed:
        print(f"\n실패한 항목:")
        for fail in failed[:10]:
            print(f"  - ID {fail['id']}: {fail['error']}")
    print(f"{'='*60}\n")

    return updated, failed


def main():
    print("="*60)
    print("🚀 캐릭터 한국어 이름 직접 패치")
    print("="*60)

    # Load names
    names_dict = load_korean_names()
    if not names_dict:
        sys.exit(1)

    # Patch
    updated, failed = patch_korean_names(names_dict)

    if failed:
        sys.exit(1)

    print("\n✅ 모든 패치가 완료되었습니다!")


if __name__ == "__main__":
    main()
