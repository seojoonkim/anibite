"""
API Dependencies
FastAPI dependencies (get_current_user, pagination, etc.)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from database import get_db, Database, dict_from_row
from utils.security import decode_access_token
from models.user import UserResponse

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_db)
) -> UserResponse:
    """
    JWT 토큰에서 현재 사용자 정보 추출
    인증이 필요한 엔드포인트에서 사용
    """
    token = credentials.credentials

    # 토큰 디코드
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # 사용자 조회
    user_row = db.execute_query(
        "SELECT * FROM users WHERE username = ?",
        (username,),
        fetch_one=True
    )

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Database = Depends(get_db)
) -> Optional[UserResponse]:
    """
    선택적 인증 (로그인 안 해도 접근 가능, 하면 사용자 정보 제공)
    """
    if credentials is None:
        return None

    token = credentials.credentials

    # 토큰 디코드
    payload = decode_access_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    # 사용자 조회
    user_row = db.execute_query(
        "SELECT * FROM users WHERE username = ?",
        (username,),
        fetch_one=True
    )

    if user_row is None:
        return None

    user_dict = dict_from_row(user_row)
    return UserResponse(**user_dict)
