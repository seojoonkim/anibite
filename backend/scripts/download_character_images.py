"""
Download character images from AniList and upload to R2
캐릭터 이미지를 AniList에서 다운로드하여 R2에 업로드
"""
import os
import sys
import requests
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db
from utils.r2_storage import upload_to_r2

def download_and_upload_character_images(limit=None):
    """
    Download character images from AniList and upload to R2
    
    Args:
        limit: Maximum number of images to process (None for all)
    """
    # Get all characters with image URLs
    query = """
        SELECT DISTINCT c.id, c.image_url, c.name_full
        FROM character c
        INNER JOIN character_ratings cr ON c.id = cr.character_id
        WHERE c.image_url IS NOT NULL 
        AND c.image_url LIKE '%anilist.co%'
        AND c.image_local IS NULL
        ORDER BY c.favourites DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    characters = db.execute_query(query)
    
    if not characters:
        print("No characters found to process")
        return
    
    print(f"Found {len(characters)} characters to process")
    
    success_count = 0
    error_count = 0
    
    for idx, char in enumerate(characters, 1):
        char_id = char['id']
        image_url = char['image_url']
        name = char['name_full']
        
        print(f"\n[{idx}/{len(characters)}] Processing: {name} (ID: {char_id})")
        print(f"  URL: {image_url}")
        
        try:
            # Download image from AniList
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension from URL or content-type
            ext = 'jpg'
            if '.png' in image_url.lower():
                ext = 'png'
            elif '.webp' in image_url.lower():
                ext = 'webp'
            elif '.gif' in image_url.lower():
                ext = 'gif'
            
            # Upload to R2
            r2_path = f"images/characters/{char_id}.{ext}"
            content_type = f"image/{ext}"
            
            print(f"  Uploading to R2: {r2_path}")
            upload_to_r2(response.content, r2_path, content_type)
            
            # Update database with local path
            db.execute_query(
                "UPDATE character SET image_local = ? WHERE id = ?",
                (r2_path, char_id)
            )
            
            success_count += 1
            print(f"  ✅ Success! ({success_count} total)")
            
            # Rate limiting - be nice to AniList
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            error_count += 1
            print(f"  ❌ Download error: {e}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Upload error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total: {len(characters)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Process top 100 most popular characters first
    # Change limit to None to process all
    download_and_upload_character_images(limit=100)
