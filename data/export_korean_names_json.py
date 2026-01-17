#!/usr/bin/env python3
"""
로컬 DB에서 한국어 이름을 JSON 파일로 export
이 JSON 파일을 Railway에 업로드하고 patch_korean_names_direct.py로 패치
"""
import sys
import os
import json
from pathlib import Path

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# JSON 파일 경로
OUTPUT_JSON = Path(__file__).parent.parent / "backend" / "scripts" / "korean_names_patch.json"


def export_korean_names():
    """로컬 DB에서 한국어 이름 export"""
    print("\n📋 로컬 DB에서 한국어 이름 추출 중...")

    query = """
        SELECT id, name_full, name_korean
        FROM character
        WHERE name_korean IS NOT NULL
          AND name_korean != ''
          AND LENGTH(name_korean) >= 2
        ORDER BY favourites DESC
    """

    characters = db.execute_query(query)

    if not characters:
        print("❌ 한국어 이름이 있는 캐릭터를 찾을 수 없습니다.")
        return None

    names_dict = {}
    for char in characters:
        char_id = char['id'] if isinstance(char, dict) else char[0]
        name_full = char['name_full'] if isinstance(char, dict) else char[1]
        name_korean = char['name_korean'] if isinstance(char, dict) else char[2]

        names_dict[str(char_id)] = name_korean

    print(f"✅ 총 {len(names_dict)}개 캐릭터의 한국어 이름을 추출했습니다.")

    # Save to JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(names_dict, f, ensure_ascii=False, indent=2)

    print(f"\n💾 JSON 파일 저장됨: {OUTPUT_JSON}")
    print(f"   파일 크기: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")

    # 샘플 출력
    print("\n샘플 (처음 10개):")
    for i, (char_id, korean_name) in enumerate(list(names_dict.items())[:10]):
        print(f"  {char_id}: {korean_name}")

    return names_dict


def main():
    print("="*60)
    print("🚀 한국어 이름 JSON export")
    print("="*60)

    names_dict = export_korean_names()
    if not names_dict:
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ Export 완료!")
    print(f"\n다음 단계:")
    print(f"1. {OUTPUT_JSON} 파일을 확인")
    print(f"2. 이 파일을 Railway 프로젝트에 포함시켜 배포")
    print(f"3. Railway에서 patch_korean_names_direct.py 실행")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
