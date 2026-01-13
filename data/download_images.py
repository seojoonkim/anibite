"""
추가 이미지 다운로드 스크립트
Phase 2: 캐릭터/성우/스태프/배너 이미지 다운로드
"""

import sqlite3
import os
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = 'anime.db'

# 이미지 저장 경로
IMAGE_PATHS = {
    'covers': 'images/covers',
    'banners': 'images/banners',
    'characters': 'images/characters',
    'staff': 'images/staff',
}

def download_image(url: str, local_path: str) -> bool:
    """이미지 다운로드"""
    if not url or os.path.exists(local_path):
        return False
    
    try:
        urllib.request.urlretrieve(url, local_path)
        return True
    except Exception as e:
        print(f"Failed: {local_path} - {e}")
        return False

def download_banner_images():
    """애니 배너 이미지 다운로드"""
    os.makedirs(IMAGE_PATHS['banners'], exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, banner_image_url FROM anime WHERE banner_image_url IS NOT NULL')
    items = cursor.fetchall()
    conn.close()
    
    print(f"\n🖼️ Downloading {len(items)} banner images...")
    
    downloaded = 0
    for idx, (item_id, url) in enumerate(items, 1):
        ext = url.split('.')[-1].split('?')[0][:4]
        local_path = f"{IMAGE_PATHS['banners']}/{item_id}.{ext}"
        
        if download_image(url, local_path):
            downloaded += 1
        
        if idx % 100 == 0:
            print(f"   Progress: {idx}/{len(items)}")
        
        time.sleep(0.05)
    
    print(f"✅ Banner images: {downloaded} downloaded")

def download_character_images():
    """캐릭터 이미지 다운로드"""
    os.makedirs(IMAGE_PATHS['characters'], exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, image_url FROM character WHERE image_url IS NOT NULL')
    items = cursor.fetchall()
    conn.close()
    
    print(f"\n🖼️ Downloading {len(items)} character images...")
    
    downloaded = 0
    for idx, (item_id, url) in enumerate(items, 1):
        ext = url.split('.')[-1].split('?')[0][:4]
        local_path = f"{IMAGE_PATHS['characters']}/{item_id}.{ext}"
        
        if download_image(url, local_path):
            downloaded += 1
        
        if idx % 500 == 0:
            print(f"   Progress: {idx}/{len(items)}")
        
        time.sleep(0.05)
    
    print(f"✅ Character images: {downloaded} downloaded")

def download_staff_images():
    """스태프/성우 이미지 다운로드"""
    os.makedirs(IMAGE_PATHS['staff'], exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, image_url FROM staff WHERE image_url IS NOT NULL')
    items = cursor.fetchall()
    conn.close()
    
    print(f"\n🖼️ Downloading {len(items)} staff images...")
    
    downloaded = 0
    for idx, (item_id, url) in enumerate(items, 1):
        ext = url.split('.')[-1].split('?')[0][:4]
        local_path = f"{IMAGE_PATHS['staff']}/{item_id}.{ext}"
        
        if download_image(url, local_path):
            downloaded += 1
        
        if idx % 500 == 0:
            print(f"   Progress: {idx}/{len(items)}")
        
        time.sleep(0.05)
    
    print(f"✅ Staff images: {downloaded} downloaded")

def download_all_images():
    """모든 이미지 다운로드"""
    print("=" * 50)
    print("📥 DOWNLOADING ALL IMAGES")
    print("=" * 50)
    
    download_banner_images()
    download_character_images()
    download_staff_images()
    
    # 용량 계산
    print("\n📊 Image storage summary:")
    for name, path in IMAGE_PATHS.items():
        if os.path.exists(path):
            size = sum(
                os.path.getsize(os.path.join(path, f))
                for f in os.listdir(path)
            ) / (1024 * 1024)
            count = len(os.listdir(path))
            print(f"   {name}: {count} files, {size:.1f} MB")

def update_local_paths():
    """DB에 로컬 경로 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 캐릭터 이미지 경로 업데이트
    for f in os.listdir(IMAGE_PATHS['characters']):
        char_id = f.split('.')[0]
        local_path = f"{IMAGE_PATHS['characters']}/{f}"
        cursor.execute(
            'UPDATE character SET image_local = ? WHERE id = ?',
            (local_path, char_id)
        )
    
    # 스태프 이미지 경로 업데이트
    for f in os.listdir(IMAGE_PATHS['staff']):
        staff_id = f.split('.')[0]
        local_path = f"{IMAGE_PATHS['staff']}/{f}"
        cursor.execute(
            'UPDATE staff SET image_local = ? WHERE id = ?',
            (local_path, staff_id)
        )
    
    conn.commit()
    conn.close()
    print("✅ Local paths updated in database")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'banners':
            download_banner_images()
        elif cmd == 'characters':
            download_character_images()
        elif cmd == 'staff':
            download_staff_images()
        elif cmd == 'all':
            download_all_images()
            update_local_paths()
        else:
            print("Usage: python download_images.py [banners|characters|staff|all]")
    else:
        print("🖼️ Image Download Script")
        print("=" * 40)
        print("Usage:")
        print("  python download_images.py banners    - Download anime banners")
        print("  python download_images.py characters - Download character images")
        print("  python download_images.py staff      - Download staff images")
        print("  python download_images.py all        - Download all images")
