"""
Google OAuth Service
Google 로그인/회원가입 처리
"""
from typing import Dict
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from database import db, dict_from_row
from utils.security import create_access_token
from utils.user_helpers import set_default_avatar
from models.user import UserResponse, TokenResponse
from config import GOOGLE_CLIENT_ID


async def verify_google_token(credential: str) -> Dict[str, str]:
    """
    Google ID 토큰 검증

    Args:
        credential: Google ID 토큰

    Returns:
        Dict: Google 사용자 정보 (sub, email, name, picture)

    Raises:
        HTTPException: 토큰 검증 실패
    """
    try:
        # Google 토큰 검증
        idinfo = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # 발급자 확인
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )

        # 필수 정보 추출
        google_user_info = {
            'oauth_id': idinfo['sub'],  # Google 사용자 고유 ID
            'email': idinfo.get('email', ''),
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', ''),
            'email_verified': idinfo.get('email_verified', False)
        }

        if not google_user_info['email']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )

        return google_user_info

    except ValueError as e:
        # 토큰 검증 실패
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        # 기타 오류
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying Google token: {str(e)}"
        )


async def google_login_or_register(google_user_info: Dict[str, str], preferred_language: str = 'en') -> TokenResponse:
    """
    Google OAuth 로그인 또는 회원가입

    Args:
        google_user_info: Google 사용자 정보
        preferred_language: 선호 언어 (ko, en, ja)

    Returns:
        TokenResponse: JWT 토큰 및 사용자 정보
    """
    oauth_id = google_user_info['oauth_id']
    email = google_user_info['email']
    name = google_user_info['name']
    picture = google_user_info['picture']

    # 1. 기존 OAuth 사용자 확인
    existing_oauth_user = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.oauth_provider = 'google' AND u.oauth_id = ?
        """,
        (oauth_id,),
        fetch_one=True
    )

    if existing_oauth_user:
        # 기존 OAuth 사용자 → 로그인 처리 (프로필 사진은 유지)
        user_dict = dict_from_row(existing_oauth_user)
        user_id = user_dict['id']

        # 프로필 사진 업데이트 안 함 - 사용자가 설정한 캐릭터 이미지 유지
        # avatar_url이 없으면 5점 캐릭터 이미지 자동 설정
        user_dict = set_default_avatar(user_dict, db)

        user_response = UserResponse(**user_dict)
        access_token = create_access_token(data={"sub": user_response.username})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    # 2. 같은 이메일의 기존 계정이 있으면 Google OAuth 통합
    existing_email_user = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.email = ?
        """,
        (email,),
        fetch_one=True
    )

    if existing_email_user:
        # 기존 계정에 Google OAuth 연동 (계정 통합)
        user_dict = dict_from_row(existing_email_user)
        user_id = user_dict['id']

        # Google OAuth 정보 업데이트 (프로필 사진은 유지)
        db.execute_query(
            """
            UPDATE users
            SET oauth_provider = 'google',
                oauth_id = ?,
                is_verified = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (oauth_id, user_id)
        )

        # 업데이트된 사용자 정보 다시 조회
        updated_user = db.execute_query(
            """
            SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
            FROM users u
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE u.id = ?
            """,
            (user_id,),
            fetch_one=True
        )

        user_dict = dict_from_row(updated_user)
        user_dict = set_default_avatar(user_dict, db)
        user_response = UserResponse(**user_dict)
        access_token = create_access_token(data={"sub": user_dict['username']})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    # 3. 신규 Google 사용자 → 회원가입 처리
    # username 생성 (이메일 기반, 중복 방지)
    base_username = email.split('@')[0]
    username = base_username
    counter = 1

    # username 중복 확인 및 고유화
    while True:
        existing_username = db.execute_query(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            fetch_one=True
        )
        if not existing_username:
            break
        username = f"{base_username}{counter}"
        counter += 1

    # 사용자 생성 (비밀번호 없음, 자동 이메일 인증, 프로필 사진 없음)
    user_id = db.execute_insert(
        """
        INSERT INTO users (username, email, password_hash, display_name, avatar_url,
                          preferred_language, oauth_provider, oauth_id,
                          is_verified, created_at, updated_at)
        VALUES (?, ?, NULL, ?, NULL, ?, 'google', ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (username, email, name, preferred_language, oauth_id)
    )

    # 사용자 통계 초기화
    db.execute_insert(
        """
        INSERT INTO user_stats (user_id, total_rated, total_want_to_watch, total_pass,
                                average_rating, total_reviews, total_character_ratings, total_watch_time_minutes,
                                otaku_score, updated_at)
        VALUES (?, 0, 0, 0, NULL, 0, 0, 0, 0.0, CURRENT_TIMESTAMP)
        """,
        (user_id,)
    )

    # 생성된 사용자 정보 조회
    user_row = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    user_dict = dict_from_row(user_row)
    user_dict = set_default_avatar(user_dict, db)
    user_response = UserResponse(**user_dict)

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )
