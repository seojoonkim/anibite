#!/usr/bin/env python3
"""
로컬 DB에서 한국어 이름이 있는 모든 캐릭터를 추출하여 서버로 전송
"""
import sys
import os
import json
import requests
import argparse
from pathlib import Path

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# 기본 서버 URL
DEFAULT_SERVER_URL = "https://anipass.io"


def extract_all_korean_names():
    """로컬 DB에서 한국어 이름이 있는 모든 캐릭터 추출"""
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

    # 샘플 출력
    print("\n샘플 (처음 10개):")
    for i, (char_id, korean_name) in enumerate(list(names_dict.items())[:10]):
        print(f"  {char_id}: {korean_name}")

    return names_dict


def patch_to_server(server_url, names_dict, batch_size=100, dry_run=False):
    """서버에 한국어 이름 패치"""
    api_url = f"{server_url}/api/admin/patch-korean-names"

    total_names = len(names_dict)
    print(f"\n📊 총 {total_names}개 캐릭터를 패치합니다.")

    if dry_run:
        print("\n🔍 DRY RUN 모드 - 실제 전송하지 않습니다.")
        print(f"\nAPI URL: {api_url}")
        print(f"전송할 데이터 크기: {len(json.dumps({'names': names_dict}))} bytes")
        return True

    # 배치로 나누어 전송
    batches = []
    items = list(names_dict.items())

    for i in range(0, len(items), batch_size):
        batch = dict(items[i:i + batch_size])
        batches.append(batch)

    print(f"\n📦 {len(batches)}개 배치로 나누어 전송합니다 (배치당 최대 {batch_size}개)")

    total_updated = 0
    total_failed = 0

    for idx, batch in enumerate(batches, 1):
        print(f"\n배치 {idx}/{len(batches)} 전송 중... ({len(batch)}개)")

        payload = {"names": batch}

        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=120,  # 큰 배치를 위해 타임아웃 증가
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                updated = result.get("updated", 0)
                failed = result.get("failed", [])

                total_updated += updated
                total_failed += len(failed)

                print(f"  ✅ 성공: {updated}개 업데이트")
                if failed:
                    print(f"  ⚠️  실패: {len(failed)}개")
                    for fail in failed[:3]:  # 처음 3개만 표시
                        print(f"    - ID {fail.get('id', 'unknown')}: {fail.get('error', 'unknown error')}")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}")
                total_failed += len(batch)

        except requests.Timeout:
            print(f"  ❌ 타임아웃 - 배치 크기를 줄이거나 나중에 다시 시도하세요")
            total_failed += len(batch)
        except Exception as e:
            print(f"  ❌ 에러: {e}")
            total_failed += len(batch)

    print(f"\n{'='*60}")
    print(f"✅ 패치 완료!")
    print(f"  총 시도: {total_names}개")
    print(f"  성공: {total_updated}개")
    print(f"  실패: {total_failed}개")
    print(f"  성공률: {total_updated/total_names*100:.1f}%" if total_names > 0 else "  성공률: N/A")
    print(f"{'='*60}\n")

    return total_failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="로컬 DB의 모든 한국어 이름을 서버에 패치"
    )
    parser.add_argument(
        "--server",
        type=str,
        default=DEFAULT_SERVER_URL,
        help=f"서버 URL (기본값: {DEFAULT_SERVER_URL})"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="배치당 전송할 캐릭터 수 (기본값: 500)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 전송하지 않고 테스트만 수행"
    )
    args = parser.parse_args()

    print("="*60)
    print("🚀 로컬 DB → 서버 한국어 이름 패치")
    print(f"   서버: {args.server}")
    print(f"   배치 크기: {args.batch_size}")
    if args.dry_run:
        print("   모드: DRY RUN (테스트)")
    print("="*60)

    # DB에서 한국어 이름 추출
    names_dict = extract_all_korean_names()
    if not names_dict:
        sys.exit(1)

    # 서버에 패치
    success = patch_to_server(args.server, names_dict, args.batch_size, args.dry_run)

    if not success and not args.dry_run:
        print("\n⚠️  일부 패치가 실패했습니다. 위 에러 메시지를 확인하세요.")
        sys.exit(1)

    if not args.dry_run:
        print("\n✅ 모든 패치가 완료되었습니다!")


if __name__ == "__main__":
    main()
