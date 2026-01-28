#!/usr/bin/env python3
"""
Railway DB Upload Script
현재 로컬 anime.db를 Railway에 업로드합니다.

사용법:
    python3 scripts/upload_db_to_railway.py
"""
import os
import sys
import requests
from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "anime.db"

# Railway 백엔드 URL (환경에 맞게 변경)
RAILWAY_URL = "https://anipass-backend-production.up.railway.app"

def main():
    print("=" * 60)
    print("Railway DB Upload Script")
    print("=" * 60)

    # DB 파일 확인
    if not DB_PATH.exists():
        print(f"❌ Error: DB file not found at {DB_PATH}")
        sys.exit(1)

    db_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ Found DB file: {DB_PATH}")
    print(f"📦 Size: {db_size:.2f} MB")

    # 경고
    print("\n⚠️  WARNING:")
    print("   This will OVERWRITE the database on Railway!")
    print("   Make sure you have backed up the current Railway DB if needed.")

    response = input("\n🤔 Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled.")
        sys.exit(0)

    print("\n📤 Uploading DB to Railway...")
    print("   (This may take a few minutes for large files)")

    try:
        # Railway 백엔드 API를 통해 업로드
        # 실제 구현은 Railway API 또는 SSH를 통해 수행
        print("\n⚠️  Manual Upload Required:")
        print("\n   Option 1: Railway CLI")
        print("   ```bash")
        print("   railway login")
        print("   railway link")
        print(f"   railway run bash -c 'cat > /app/data/anime.db' < {DB_PATH}")
        print("   ```")

        print("\n   Option 2: SCP (if SSH enabled)")
        print("   ```bash")
        print(f"   scp {DB_PATH} railway:/app/data/anime.db")
        print("   ```")

        print("\n   Option 3: Admin Upload Endpoint (if implemented)")
        print(f"   curl -X POST {RAILWAY_URL}/api/admin/upload-db \\")
        print(f"        -F 'file=@{DB_PATH}' \\")
        print("        -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'")

        print("\n💡 Tip: Railway CLI 방법이 가장 간단합니다!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
