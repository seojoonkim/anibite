"""
이메일 전송 서비스

개발 환경: 콘솔에 링크 출력
프로덕션: 실제 이메일 전송 (SendGrid, AWS SES 등)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 환경 변수에서 설정 가져오기
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@anipass.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5176')


def send_verification_email(email: str, username: str, verification_token: str) -> bool:
    """
    이메일 인증 링크 전송

    Args:
        email: 수신자 이메일
        username: 사용자명
        verification_token: 인증 토큰

    Returns:
        성공 여부
    """
    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"

    subject = "[AniPass] 이메일 인증을 완료해주세요"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #3498DB;">AniPass 회원가입을 환영합니다! 🎉</h2>
            <p>안녕하세요, <strong>{username}</strong>님!</p>
            <p>AniPass 회원가입을 완료하려면 아래 버튼을 클릭하여 이메일 인증을 진행해주세요.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}"
                   style="background-color: #3498DB;
                          color: white;
                          padding: 12px 30px;
                          text-decoration: none;
                          border-radius: 5px;
                          display: inline-block;
                          font-weight: bold;">
                    이메일 인증하기
                </a>
            </div>

            <p style="color: #666; font-size: 14px;">
                버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:<br>
                <a href="{verification_link}" style="color: #3498DB;">{verification_link}</a>
            </p>

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                ⏰ 이 링크는 24시간 동안 유효합니다.<br>
                📧 본인이 요청하지 않았다면 이 이메일을 무시하세요.
            </p>

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                © 2024 AniPass. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    # 개발 환경: 콘솔에 출력
    if ENVIRONMENT == 'development':
        logger.info("=" * 80)
        logger.info("📧 [개발 모드] 이메일 인증 링크")
        logger.info(f"수신자: {email}")
        logger.info(f"사용자: {username}")
        logger.info(f"인증 링크: {verification_link}")
        logger.info("=" * 80)
        print("\n" + "=" * 80)
        print("📧 이메일 인증 링크가 생성되었습니다!")
        print(f"👤 사용자: {username} ({email})")
        print(f"🔗 인증 링크:")
        print(f"   {verification_link}")
        print("=" * 80 + "\n")
        return True

    # 프로덕션 환경: 실제 이메일 전송
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.error("SMTP 설정이 없습니다. 환경 변수를 확인하세요.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = email

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"인증 이메일 전송 성공: {email}")
        return True

    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
        return False


def send_password_reset_email(email: str, username: str, reset_token: str) -> bool:
    """
    비밀번호 재설정 이메일 전송 (향후 구현용)
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    if ENVIRONMENT == 'development':
        print("\n" + "=" * 80)
        print("🔑 비밀번호 재설정 링크가 생성되었습니다!")
        print(f"👤 사용자: {username} ({email})")
        print(f"🔗 재설정 링크:")
        print(f"   {reset_link}")
        print("=" * 80 + "\n")
        return True

    # TODO: 실제 이메일 전송 구현
    return True
