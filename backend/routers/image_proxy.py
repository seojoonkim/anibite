"""
Image Proxy Router
이미지 프록시 - R2에 없으면 AniList에서 다운로드 후 캐싱
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response
import requests
from utils.r2_storage import upload_to_r2, check_r2_object_exists, get_r2_presigned_url
from database import db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/images/characters/{character_id}.{ext}")
async def get_character_image(character_id: int, ext: str):
    """
    Get character image - auto-download from AniList if not in R2
    캐릭터 이미지 가져오기 - R2에 없으면 AniList에서 자동 다운로드
    """
    r2_path = f"images/characters/{character_id}.{ext}"
    
    # Check if image exists in R2
    if check_r2_object_exists(r2_path):
        # Redirect to R2 public URL
        from config import IMAGE_BASE_URL
        return RedirectResponse(url=f"{IMAGE_BASE_URL}/{r2_path}")
    
    # Image not in R2, try to download from AniList
    logger.info(f"Image not found in R2: {r2_path}, attempting to download from AniList")
    
    # Get character's AniList image URL from database
    character = db.execute_query(
        "SELECT image_url FROM character WHERE id = ?",
        (character_id,),
        fetch_one=True
    )
    
    if not character or not character['image_url']:
        raise HTTPException(status_code=404, detail="Character not found or no image URL")
    
    anilist_url = character['image_url']
    
    try:
        # Download from AniList
        logger.info(f"Downloading from AniList: {anilist_url}")
        response = requests.get(anilist_url, timeout=10)
        response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('content-type', f'image/{ext}')
        
        # Upload to R2
        logger.info(f"Uploading to R2: {r2_path}")
        upload_to_r2(response.content, r2_path, content_type)
        
        # Update database with local path
        db.execute_query(
            "UPDATE character SET image_local = ? WHERE id = ?",
            (r2_path, character_id)
        )
        
        logger.info(f"Successfully cached image: {r2_path}")
        
        # Return the image directly
        return Response(content=response.content, media_type=content_type)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from AniList: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to download image from AniList: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to upload to R2: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cache image: {str(e)}")
