#!/usr/bin/env python3
"""
로컬에서 업데이트한 한국어 이름을 서버에 패치하는 스크립트
update_all_korean_progress.json에서 업데이트된 캐릭터들을 읽어서 서버 API로 전송
"""
import sys
import os
import json
import requests
import argparse
from pathlib import Path

# 파일 경로
PROGRESS_FILE = Path(__file__).parent / "update_all_korean_progress.json"

# 기본 서버 URL
DEFAULT_SERVER_URL = "https://anibite.com"


def load_updated_names():
    """진행 상황 파일에서 업데이트된 한국어 이름 추출"""
    if not PROGRESS_FILE.exists():
        print(f"❌ 진행 상황 파일을 찾을 수 없습니다: {PROGRESS_FILE}")
        return None

    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress = json.load(f)
    except Exception as e:
        print(f"❌ 진행 상황 파일 읽기 실패: {e}")
        return None

    updated = progress.get("updated", {})

    if not updated:
        print("⚠️  업데이트된 캐릭터가 없습니다.")
        return None

    # API 형식에 맞게 변환 (character_id: korean_name)
    names_dict = {}
    for char_id, info in updated.items():
        korean_name = info.get("new")
        if korean_name:
            names_dict[char_id] = korean_name

    return names_dict


def patch_to_server(server_url, names_dict, batch_size=100, dry_run=False):
    """서버에 한국어 이름 패치"""
    api_url = f"{server_url}/api/admin/patch-korean-names"

    total_names = len(names_dict)
    print(f"\n📊 총 {total_names}개 캐릭터를 패치합니다.")

    if dry_run:
        print("\n🔍 DRY RUN 모드 - 실제 전송하지 않습니다.")
        print("\n샘플 데이터 (처음 5개):")
        for i, (char_id, korean_name) in enumerate(list(names_dict.items())[:5]):
            print(f"  {char_id}: {korean_name}")
        print(f"\nAPI URL: {api_url}")
        print(f"전송할 데이터 크기: {len(json.dumps({'names': names_dict}))} bytes")
        return True

    # 배치로 나누어 전송 (API 타임아웃 방지)
    batches = []
    items = list(names_dict.items())

    for i in range(0, len(items), batch_size):
        batch = dict(items[i:i + batch_size])
        batches.append(batch)

    print(f"\n📦 {len(batches)}개 배치로 나누어 전송합니다 (배치당 {batch_size}개)")

    total_updated = 0
    total_failed = 0

    for idx, batch in enumerate(batches, 1):
        print(f"\n배치 {idx}/{len(batches)} 전송 중... ({len(batch)}개)")

        payload = {"names": batch}

        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=60,
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
                        print(f"    - ID {fail['id']}: {fail['error']}")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
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
    print(f"{'='*60}\n")

    return total_failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="로컬에서 업데이트한 한국어 이름을 서버에 패치"
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
        default=100,
        help="배치당 전송할 캐릭터 수 (기본값: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 전송하지 않고 테스트만 수행"
    )
    args = parser.parse_args()

    print("="*60)
    print("🚀 한국어 이름 서버 패치 스크립트")
    print(f"   서버: {args.server}")
    print(f"   배치 크기: {args.batch_size}")
    print("="*60)

    # 업데이트된 이름 로드
    names_dict = load_updated_names()
    if not names_dict:
        sys.exit(1)

    # 서버에 패치
    success = patch_to_server(args.server, names_dict, args.batch_size, args.dry_run)

    if not success and not args.dry_run:
        print("\n⚠️  일부 패치가 실패했습니다. 위 에러 메시지를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
