# 이메일 인증 설정 가이드

## 현재 상태
- ✅ 회원가입 시 즉시 인증 완료 (`is_verified=1`)
- ✅ 이메일 전송 없이 바로 로그인 가능
- ⏸️ 이메일 인증 기능 비활성화 (SMTP 미설정)

## SMTP 설정 후 이메일 인증 재도입 계획

### 1단계: SMTP 설정 (Gmail 사용)

#### Gmail 앱 비밀번호 생성
1. Gmail 계정 로그인
2. Google 계정 관리 → 보안
3. 2단계 인증 활성화 (필수)
4. "앱 비밀번호" 생성
   - 앱 선택: 메일
   - 기기 선택: 기타 (AniPass)
   - 16자리 비밀번호 복사

#### Railway 환경 변수 설정
Railway 대시보드에서 다음 환경 변수 추가:

```
ENVIRONMENT=production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-digit-app-password
FROM_EMAIL=noreply@anipass.io
FRONTEND_URL=https://anipass.io
```

⚠️ **중요**: `SMTP_PASSWORD`는 Gmail 로그인 비밀번호가 아닌 **앱 비밀번호**를 사용해야 합니다.

#### 로컬 테스트 (.env 파일)
```bash
# backend/.env
ENVIRONMENT=development  # 개발 환경에서는 콘솔 출력
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@anipass.io
FRONTEND_URL=http://localhost:5176
```

### 2단계: 이메일 전송 테스트

SMTP 설정 후 배포하면 자동으로 이메일이 전송됩니다.

#### 테스트 방법
1. Railway 환경 변수 설정
2. 배포 완료 대기
3. 새 이메일로 회원가입 시도
4. Railway 로그 확인:
   ```
   ✓ 인증 이메일 전송 성공: test@example.com
   ```
5. 받은 이메일의 인증 링크 클릭
6. 자동 로그인 확인

### 3단계: 이메일 인증 재도입

#### 코드 변경 사항

**`services/auth_service.py`** - 3곳 수정:

```python
# 1. 회원가입 시 is_verified=0으로 변경 (Line 38-48)
# 변경 전:
VALUES (?, ?, ?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)

# 변경 후:
VALUES (?, ?, ?, ?, ?, 0, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)


# 2. 회원가입 후 이메일 인증 안내 반환 (Line 61-87)
# 변경 전:
# 이메일 인증 비활성화 - 즉시 로그인 가능
# ...TokenResponse 반환

# 변경 후:
# 인증 이메일 전송
email_sent = send_verification_email(
    email=user_data.email,
    username=user_data.username,
    verification_token=verification_token
)

if not email_sent:
    # 이메일 전송 실패 시 에러 처리
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to send verification email. Please try again or contact support."
    )

# 이메일 인증 안내 메시지 반환
return {
    "message": "Registration successful! Please check your email to verify your account.",
    "email": user_data.email,
    "username": user_data.username
}


# 3. 로그인 시 이메일 인증 체크 활성화 (Line 120-125)
# 변경 전:
# 이메일 인증 체크 비활성화 (SMTP 설정 전까지)
# if not user_dict.get('is_verified', False):
#     raise HTTPException(...)

# 변경 후:
# 이메일 인증 확인
if not user_dict.get('is_verified', False):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Please verify your email before logging in. Check your inbox for the verification link."
    )
```

### 4단계: 기존 사용자 영향 방지

✅ **기존 사용자는 영향 없음**
- `scripts/verify_existing_users.py`가 서버 시작 시 자동 실행
- 기존 사용자는 모두 `is_verified=1`로 설정됨
- 기존 사용자는 계속 로그인 가능

✅ **신규 사용자만 이메일 인증 필요**
- 코드 변경 후 가입하는 사용자는 `is_verified=0`
- 이메일 인증 완료 후 로그인 가능

### 5단계: 프론트엔드 확인

다음 파일들이 이미 이메일 인증 흐름을 지원합니다:

✅ **Register.jsx** (Line 42-54)
- `requiresVerification` 플래그 처리
- EmailSent 페이지로 리디렉션

✅ **AuthContext.jsx** (Line 92-127)
- 이메일 인증 필요 시 처리
- 레거시 즉시 로그인도 지원

✅ **VerifyEmail.jsx**
- 토큰으로 이메일 인증
- 자동 로그인 처리

✅ **EmailSent.jsx**
- 이메일 확인 안내 페이지

### 6단계: 배포 체크리스트

#### 배포 전
- [ ] Railway 환경 변수 모두 설정
- [ ] `SMTP_PASSWORD`가 앱 비밀번호인지 확인
- [ ] `FRONTEND_URL`이 `https://anipass.io`인지 확인
- [ ] `FROM_EMAIL` 설정 확인
- [ ] 로컬에서 이메일 전송 테스트 완료

#### 코드 변경
- [ ] `auth_service.py` 3곳 수정
- [ ] 변경사항 커밋

#### 배포 후
- [ ] Railway 배포 완료 확인
- [ ] 새 이메일로 회원가입 테스트
- [ ] 이메일 수신 확인
- [ ] 인증 링크 클릭
- [ ] 자동 로그인 확인
- [ ] 기존 계정 로그인 확인 (영향 없는지)

### 7단계: 에러 처리

#### 이메일 전송 실패 시
현재 코드는 이메일 전송 실패해도 회원가입을 완료합니다.
이메일 인증 재도입 시, 전송 실패하면 회원가입을 롤백해야 합니다.

**개선 방안**:
```python
# 이메일 전송 실패 시 사용자 삭제
email_sent = send_verification_email(...)
if not email_sent:
    # 생성한 사용자 삭제
    db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
    db.execute_update("DELETE FROM user_stats WHERE user_id = ?", (user_id,))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to send verification email. Please try again."
    )
```

#### 토큰 만료 처리
- 현재 토큰은 24시간 유효
- 만료 시 "resend verification email" 기능 필요
- API 엔드포인트: `/api/auth/resend-verification` (이미 구현됨)

### 8단계: 모니터링

배포 후 Railway 로그에서 확인:
- 이메일 전송 성공/실패 로그
- 인증 완료 로그
- 에러 발생 여부

## 대안: SendGrid 사용 (더 안정적)

Gmail 대신 SendGrid를 사용하면 더 높은 전달률과 상세한 분석을 제공합니다.

### SendGrid 설정
1. SendGrid 가입 (무료 플랜: 하루 100통)
2. API Key 생성
3. Sender Authentication 설정
4. 환경 변수:
   ```
   SENDGRID_API_KEY=SG.xxx...xxx
   FROM_EMAIL=noreply@anipass.io
   ```

### 코드 수정 필요
`services/email_service.py`에 SendGrid 전송 로직 추가 필요

## 롤백 계획

이메일 인증 도입 후 문제 발생 시:

1. **긴급 롤백** (5분):
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **임시 해결** (관리자 API 사용):
   ```bash
   curl -X POST https://anipass-production.up.railway.app/api/admin/verify-all-users
   ```
   모든 사용자를 인증 완료 처리

3. **환경 변수만 변경**:
   Railway에서 `ENVIRONMENT=development`로 변경
   → 이메일 대신 콘솔 출력 (로그에서 링크 확인 가능)

## 요약

### 무료 옵션
1. **Gmail**: 설정 간단, 하루 500통 무료
2. **SendGrid**: 전문 서비스, 하루 100통 무료, 더 안정적

### 핵심 원칙
1. **기존 사용자 영향 없음** - 자동 인증 유지
2. **신규 사용자만 이메일 인증** - 점진적 적용
3. **에러 시 롤백 용이** - 관리자 API로 즉시 해결
4. **단계별 테스트** - 로컬 → 프로덕션 순차 진행

### 예상 소요 시간
- SMTP 설정: 10분
- 이메일 전송 테스트: 5분
- 코드 수정: 10분
- 배포 및 검증: 10분
- **총 35분**
