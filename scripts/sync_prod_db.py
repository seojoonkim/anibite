"""
Sync production database to local
프로덕션 데이터베이스를 로컬로 동기화

Usage:
    python scripts/sync_prod_db.py
    python scripts/sync_prod_db.py --prod-url https://your-railway-app.up.railway.app
"""
import os
import sys
import urllib.request
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
PROD_URL = os.getenv("PROD_API_URL", "https://anipass-backend-production.up.railway.app")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "anipass-local-dev-2024")
LOCAL_DB_PATH = Path(__file__).parent.parent / "data" / "anime.db"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def download_prod_db(prod_url: str = None, secret: str = None):
    """Download production database"""
    url = prod_url or PROD_URL
    secret = secret or ADMIN_SECRET

    download_url = f"{url}/api/admin/download-db?secret={secret}"

    print(f"Downloading from: {url}")
    print(f"Target: {LOCAL_DB_PATH}")

    # Create backup of existing local DB
    if LOCAL_DB_PATH.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"anime_backup_{timestamp}.db"
        shutil.copy2(LOCAL_DB_PATH, backup_path)
        print(f"Backup created: {backup_path}")

    # Download
    try:
        print("Downloading...")
        urllib.request.urlretrieve(download_url, str(LOCAL_DB_PATH))

        # Check file size
        file_size = LOCAL_DB_PATH.stat().st_size
        print(f"Download complete!")
        print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        if e.code == 403:
            print("Invalid secret key. Check ADMIN_SECRET environment variable.")
        elif e.code == 404:
            print("Database not found on server or endpoint doesn't exist.")
        sys.exit(1)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync production DB to local")
    parser.add_argument("--prod-url", help="Production API URL")
    parser.add_argument("--secret", help="Admin secret key")

    args = parser.parse_args()

    download_prod_db(
        prod_url=args.prod_url,
        secret=args.secret
    )
