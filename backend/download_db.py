"""
Download anime.db from temporary hosting
Run this once to populate the Railway volume with the full database
"""
import os
import urllib.request
from pathlib import Path

# Database path
DATA_DIR = Path("/app/data")
DB_PATH = DATA_DIR / "anime.db"

# Temporary download URL (replace with actual URL)
DOWNLOAD_URL = "https://ten-llamas-remain.loca.lt/anime.db"

print(f"Downloading database from: {DOWNLOAD_URL}")
print(f"Target location: {DB_PATH}")

# Create directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Download the file
try:
    print("Starting download...")
    urllib.request.urlretrieve(DOWNLOAD_URL, str(DB_PATH))

    # Check file size
    file_size = DB_PATH.stat().st_size
    print(f"✅ Download complete!")
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")

except Exception as e:
    print(f"❌ Download failed: {e}")
    exit(1)
