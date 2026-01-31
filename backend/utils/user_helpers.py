"""
User Helper Functions
사용자 관련 유틸리티 함수
"""
from typing import Optional
from database import Database, dict_from_row


def get_user_avatar_url(user_id: int, db: Database) -> Optional[str]:
    """
    사용자 프로필 사진 URL 가져오기
    avatar_url이 없으면 5점 준 캐릭터 이미지 반환
    """
    # 5점 준 캐릭터 중 가장 최근 것 가져오기
    character = db.execute_query(
        """
        SELECT c.image_url
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ? AND cr.rating = 5
        ORDER BY cr.created_at DESC
        LIMIT 1
        """,
        (user_id,),
        fetch_one=True
    )

    if character:
        return dict_from_row(character).get('image_url')

    return None


def set_default_avatar(user_dict: dict, db: Database) -> dict:
    """
    사용자 딕셔너리에 기본 아바타 설정
    avatar_url이 없으면 5점 캐릭터 이미지로 설정
    """
    if not user_dict.get('avatar_url'):
        character_avatar = get_user_avatar_url(user_dict['id'], db)
        if character_avatar:
            user_dict['avatar_url'] = character_avatar

    return user_dict
