"""
Authentication API Router
회원가입, 로그인, 사용자 정보 조회, 이메일 인증
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.user import UserRegister, UserLogin, TokenResponse, UserResponse
from services.auth_service import (
    register_user,
    login_user,
    verify_email,
    resend_verification_email
)
from api.deps import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter()


class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """
    회원가입 - 이메일 인증 필요

    - **username**: 3-20자, 영문/숫자만
    - **email**: 유효한 이메일 주소
    - **password**: 최소 8자
    - **display_name**: 표시 이름 (선택)
    - **preferred_language**: 선호 언어 (ko/en)

    Returns:
    - **message**: 회원가입 성공 메시지
    - **email**: 등록된 이메일 (인증 링크가 전송됨)
    """
    return register_user(user_data)


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    """
    로그인

    - **username**: 사용자명
    - **password**: 비밀번호

    Returns:
    - **access_token**: JWT 액세스 토큰
    - **user**: 사용자 정보
    """
    return login_user(login_data)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    Requires: Bearer token in Authorization header
    """
    return current_user


@router.get("/verify-email", response_model=TokenResponse)
def verify_user_email(token: str = Query(..., description="이메일 인증 토큰")):
    """
    이메일 인증 처리

    이메일에서 받은 링크를 통해 이 엔드포인트가 호출됩니다.

    Args:
        token: 이메일 인증 토큰

    Returns:
        TokenResponse: 인증 완료 후 JWT 액세스 토큰
    """
    return verify_email(token)


@router.post("/resend-verification")
def resend_verification(request: ResendVerificationRequest):
    """
    인증 이메일 재전송

    이메일 인증이 완료되지 않은 사용자에게 새로운 인증 이메일을 보냅니다.

    Args:
        request: 이메일 주소

    Returns:
        성공 메시지
    """
    return resend_verification_email(request.email)
