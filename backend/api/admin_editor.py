"""
Admin Editor API - Content management interface
어드민 에디터 API - 애니메이션/캐릭터 관리
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from database import db
from api.auth import get_current_user
import os
import shutil
from datetime import datetime

router = APIRouter()


class AnimeUpdate(BaseModel):
    title_korean: Optional[str] = None
    title_romaji: Optional[str] = None
    title_english: Optional[str] = None
    title_native: Optional[str] = None


class CharacterUpdate(BaseModel):
    name_korean: Optional[str] = None
    name_full: Optional[str] = None
    name_native: Optional[str] = None


def require_simon(current_user: dict = Depends(get_current_user)):
    """Require simon user"""
    if current_user["username"] != "simon":
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


@router.get("/search")
def search_content(
    q: str,
    type: str = "both",
    limit: int = 20,
    current_user: dict = Depends(require_simon)
):
    """
    검색 - 애니메이션 또는 캐릭터
    type: anime, character, both
    """
    results = {"anime": [], "characters": []}

    if type in ["anime", "both"]:
        # 애니메이션 검색 (모든 언어)
        anime_query = """
            SELECT
                id, title_korean, title_romaji, title_english, title_native,
                cover_image, format, episodes, status, season_year
            FROM anime
            WHERE title_korean LIKE ?
               OR title_romaji LIKE ?
               OR title_english LIKE ?
               OR title_native LIKE ?
            ORDER BY popularity DESC
            LIMIT ?
        """
        pattern = f"%{q}%"
        anime_results = db.execute_query(
            anime_query,
            (pattern, pattern, pattern, pattern, limit)
        )

        results["anime"] = [
            {
                "id": row[0],
                "title_korean": row[1],
                "title_romaji": row[2],
                "title_english": row[3],
                "title_native": row[4],
                "cover_image": row[5],
                "format": row[6],
                "episodes": row[7],
                "status": row[8],
                "season_year": row[9]
            }
            for row in anime_results
        ]

    if type in ["character", "both"]:
        # 캐릭터 검색 (모든 언어)
        char_query = """
            SELECT
                c.id, c.name_korean, c.name_full, c.name_native,
                c.image_large, c.favourites,
                a.id as anime_id, a.title_korean as anime_title
            FROM character c
            LEFT JOIN anime_character ac ON c.id = ac.character_id
            LEFT JOIN anime a ON ac.anime_id = a.id
            WHERE c.name_korean LIKE ?
               OR c.name_full LIKE ?
               OR c.name_native LIKE ?
            GROUP BY c.id
            ORDER BY c.favourites DESC
            LIMIT ?
        """
        pattern = f"%{q}%"
        char_results = db.execute_query(
            char_query,
            (pattern, pattern, pattern, limit)
        )

        results["characters"] = [
            {
                "id": row[0],
                "name_korean": row[1],
                "name_full": row[2],
                "name_native": row[3],
                "image_large": row[4],
                "favourites": row[5],
                "anime_id": row[6],
                "anime_title": row[7]
            }
            for row in char_results
        ]

    return results


@router.get("/anime/{anime_id}")
def get_anime_detail(
    anime_id: int,
    current_user: dict = Depends(require_simon)
):
    """애니메이션 상세 정보"""
    query = """
        SELECT
            id, title_korean, title_romaji, title_english, title_native,
            cover_image, cover_image_large, banner_image,
            format, episodes, status, season, season_year,
            description, average_score, popularity
        FROM anime
        WHERE id = ?
    """
    result = db.execute_query(query, (anime_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Anime not found")

    row = result[0]
    return {
        "id": row[0],
        "title_korean": row[1],
        "title_romaji": row[2],
        "title_english": row[3],
        "title_native": row[4],
        "cover_image": row[5],
        "cover_image_large": row[6],
        "banner_image": row[7],
        "format": row[8],
        "episodes": row[9],
        "status": row[10],
        "season": row[11],
        "season_year": row[12],
        "description": row[13],
        "average_score": row[14],
        "popularity": row[15]
    }


@router.patch("/anime/{anime_id}")
def update_anime(
    anime_id: int,
    data: AnimeUpdate,
    current_user: dict = Depends(require_simon)
):
    """애니메이션 정보 수정"""
    # 업데이트할 필드만 선택
    updates = {}
    if data.title_korean is not None:
        updates["title_korean"] = data.title_korean
    if data.title_romaji is not None:
        updates["title_romaji"] = data.title_romaji
    if data.title_english is not None:
        updates["title_english"] = data.title_english
    if data.title_native is not None:
        updates["title_native"] = data.title_native

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # SQL 생성
    set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [anime_id]

    query = f"""
        UPDATE anime
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """

    db.execute_update(query, tuple(values))

    return {"message": "Anime updated successfully", "updated_fields": list(updates.keys())}


@router.get("/character/{character_id}")
def get_character_detail(
    character_id: int,
    current_user: dict = Depends(require_simon)
):
    """캐릭터 상세 정보"""
    query = """
        SELECT
            id, name_korean, name_full, name_native, name_alternative,
            image_medium, image_large,
            gender, age, description, favourites
        FROM character
        WHERE id = ?
    """
    result = db.execute_query(query, (character_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Character not found")

    row = result[0]
    return {
        "id": row[0],
        "name_korean": row[1],
        "name_full": row[2],
        "name_native": row[3],
        "name_alternative": row[4],
        "image_medium": row[5],
        "image_large": row[6],
        "gender": row[7],
        "age": row[8],
        "description": row[9],
        "favourites": row[10]
    }


@router.patch("/character/{character_id}")
def update_character(
    character_id: int,
    data: CharacterUpdate,
    current_user: dict = Depends(require_simon)
):
    """캐릭터 정보 수정"""
    # 업데이트할 필드만 선택
    updates = {}
    if data.name_korean is not None:
        updates["name_korean"] = data.name_korean
    if data.name_full is not None:
        updates["name_full"] = data.name_full
    if data.name_native is not None:
        updates["name_native"] = data.name_native

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # SQL 생성
    set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [character_id]

    query = f"""
        UPDATE character
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """

    db.execute_update(query, tuple(values))

    # activities 테이블도 업데이트 (캐릭터 이름 변경 시)
    if "name_korean" in updates:
        db.execute_update("""
            UPDATE activities
            SET item_title_korean = ?
            WHERE activity_type IN ('character_rating', 'character_review')
              AND item_id = ?
        """, (updates["name_korean"], character_id))

    return {"message": "Character updated successfully", "updated_fields": list(updates.keys())}


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    type: str = "character",  # anime or character
    current_user: dict = Depends(require_simon)
):
    """이미지 업로드"""
    # 파일 확장자 확인
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 저장 경로
    upload_dir = f"uploads/admin/{type}"
    os.makedirs(upload_dir, exist_ok=True)

    # 고유 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    # 파일 저장
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # URL 반환
    file_url = f"/{file_path}"

    return {
        "message": "File uploaded successfully",
        "url": file_url,
        "filename": filename
    }
