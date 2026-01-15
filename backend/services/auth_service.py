"""
Authentication Service
회원가입, 로그인, 사용자 관리
"""
from typing import Optional
from datetime import datetime, timedelta
import secrets
from fastapi import HTTPException, status
from database import db, dict_from_row
from utils.security import hash_password, verify_password, create_access_token
from models.user import UserRegister, UserLogin, UserResponse, TokenResponse
from services.email_service import send_verification_email


def register_user(user_data: UserRegister) -> dict:
    """회원가입 - 이메일 인증 필요"""

    # 중복 확인
    existing_user = db.execute_query(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (user_data.username, user_data.email),
        fetch_one=True
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )

    # 비밀번호 해싱
    hashed_password = hash_password(user_data.password)

    # 인증 토큰 생성 (24시간 유효)
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.now() + timedelta(hours=24)

    # 사용자 생성 (is_verified=1, 이메일 인증 자동 완료 - SMTP 설정 전까지)
    user_id = db.execute_insert(
        """
        INSERT INTO users (username, email, password_hash, display_name,
                          preferred_language, is_verified, verification_token,
                          verification_token_expires, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (user_data.username, user_data.email, hashed_password, user_data.display_name,
         user_data.preferred_language, verification_token, token_expires.isoformat())
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

    # 이메일 인증 비활성화 - 즉시 로그인 가능
    # (SMTP 설정 후 이메일 인증 재활성화 예정)

    # 사용자 정보 조회 (otaku_score 포함)
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
    user_response = UserResponse(**user_dict)

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": str(user_id)})

    # 즉시 로그인 처리
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


def login_user(login_data: UserLogin) -> TokenResponse:
    """로그인 (사용자명 또는 이메일)"""

    # 사용자 조회 (username 또는 email) + otaku_score
    user_row = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.username = ? OR u.email = ?
        """,
        (login_data.username, login_data.username),
        fetch_one=True
    )

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    user_dict = dict_from_row(user_row)

    # 비밀번호 확인
    if not verify_password(login_data.password, user_dict['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 이메일 인증 체크 비활성화 (SMTP 설정 전까지)
    # if not user_dict.get('is_verified', False):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Please verify your email before logging in. Check your inbox for the verification link."
    #     )

    user = UserResponse(**user_dict)

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.username})

    return TokenResponse(access_token=access_token, user=user)


def get_user_by_id(user_id: int) -> Optional[UserResponse]:
    """ID로 사용자 조회"""
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

    if user_row is None:
        return None

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)


def get_user_by_username(username: str) -> Optional[UserResponse]:
    """Username으로 사용자 조회"""
    user_row = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.username = ?
        """,
        (username,),
        fetch_one=True
    )

    if user_row is None:
        return None

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)


def update_user_profile(user_id: int, display_name: Optional[str] = None, email: Optional[str] = None) -> UserResponse:
    """사용자 프로필 업데이트 (표시 이름, 이메일)"""

    # 이메일 중복 확인 (다른 사용자가 사용중인지)
    if email:
        existing_user = db.execute_query(
            "SELECT id FROM users WHERE email = ? AND id != ?",
            (email, user_id),
            fetch_one=True
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # 업데이트할 필드 구성
    update_fields = []
    params = []

    if display_name is not None:
        update_fields.append("display_name = ?")
        params.append(display_name)

    if email is not None:
        update_fields.append("email = ?")
        params.append(email)

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)

    # 업데이트 실행
    db.execute_query(
        f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
        tuple(params)
    )

    # 업데이트된 사용자 정보 반환 (with otaku_score)
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

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)


def update_user_password(user_id: int, current_password: str, new_password: str) -> bool:
    """사용자 비밀번호 변경"""

    # 현재 사용자 조회
    user_row = db.execute_query(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
        fetch_one=True
    )

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_dict = dict_from_row(user_row)

    # 현재 비밀번호 확인
    if not verify_password(current_password, user_dict['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # 새 비밀번호 해싱
    new_hashed_password = hash_password(new_password)

    # 비밀번호 업데이트
    db.execute_query(
        "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_hashed_password, user_id)
    )

    return True


def update_user_avatar(user_id: int, avatar_url: str) -> UserResponse:
    """사용자 프로필 사진 업데이트"""

    # 업데이트 실행
    db.execute_query(
        "UPDATE users SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (avatar_url, user_id)
    )

    # 업데이트된 사용자 정보 반환 (with otaku_score)
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

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)


def verify_email(token: str) -> TokenResponse:
    """
    이메일 인증 처리
    
    Args:
        token: 인증 토큰
        
    Returns:
        TokenResponse: 인증 완료 후 JWT 토큰
    """
    # 토큰으로 사용자 조회
    user_row = db.execute_query(
        "SELECT * FROM users WHERE verification_token = ?",
        (token,),
        fetch_one=True
    )
    
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user_dict = dict_from_row(user_row)
    
    # 이미 인증된 사용자
    if user_dict.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # 토큰 만료 확인
    token_expires = datetime.fromisoformat(user_dict['verification_token_expires'])
    if datetime.now() > token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired. Please request a new one."
        )
    
    # 사용자 인증 처리
    db.execute_query(
        """
        UPDATE users 
        SET is_verified = 1,
            verification_token = NULL,
            verification_token_expires = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_dict['id'],),
        fetch_one=False
    )
    
    # 인증된 사용자 정보 다시 조회 (with otaku_score)
    user_row = db.execute_query(
        """
        SELECT u.*, COALESCE(us.otaku_score, 0.0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.id = ?
        """,
        (user_dict['id'],),
        fetch_one=True
    )

    user_dict = dict_from_row(user_row)
    user = UserResponse(**user_dict)
    
    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.username})
    
    return TokenResponse(access_token=access_token, user=user)


def resend_verification_email(email: str) -> dict:
    """
    인증 이메일 재전송
    
    Args:
        email: 사용자 이메일
        
    Returns:
        dict: 성공 메시지
    """
    # 사용자 조회
    user_row = db.execute_query(
        "SELECT * FROM users WHERE email = ?",
        (email,),
        fetch_one=True
    )
    
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_dict = dict_from_row(user_row)
    
    # 이미 인증된 사용자
    if user_dict.get('is_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # 새 인증 토큰 생성
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.now() + timedelta(hours=24)
    
    # 토큰 업데이트
    db.execute_query(
        """
        UPDATE users 
        SET verification_token = ?,
            verification_token_expires = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (verification_token, token_expires.isoformat(), user_dict['id']),
        fetch_one=False
    )
    
    # 인증 이메일 재전송
    send_verification_email(
        email=user_dict['email'],
        username=user_dict['username'],
        verification_token=verification_token
    )
    
    return {"message": "Verification email sent"}
