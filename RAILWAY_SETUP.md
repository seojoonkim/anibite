# Railway 배포 가이드

AniPass 백엔드를 Railway에 배포하는 방법입니다.

## 1. 프로젝트 연결

1. [Railway Dashboard](https://railway.app/dashboard)에 로그인
2. "New Project" → "Deploy from GitHub repo" 선택
3. `anipass` 저장소 선택

## 2. 환경 변수 설정

Railway 프로젝트 Settings → Variables에서 다음 환경 변수를 추가:

### 필수 환경 변수

```bash
# JWT Secret Key (보안 키 - 아래 명령어로 생성)
# 로컬에서: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-here

# 프론트엔드 URL (CORS 설정)
PRODUCTION_ORIGIN=https://anipass.io
```

### 선택 환경 변수

```bash
# Cloudflare R2 이미지 URL
# R2 버킷을 anipass.io 도메인에 연결한 경우:
IMAGE_BASE_URL=https://images.anipass.io
# 또는 R2 public URL: https://pub-xxxxx.r2.dev

# 커스텀 데이터베이스 경로 (기본값: /app/data/anime.db)
DATABASE_PATH=/data/anime.db
```

## 3. 볼륨 마운트 (데이터베이스 영구 저장)

Railway는 기본적으로 재배포 시 파일이 삭제됩니다. 데이터베이스를 영구 저장하려면:

### 옵션 A: Railway Volume 사용 (권장)

1. Railway 프로젝트 → Variables 탭
2. "Add Volume" 클릭
3. Mount Path: `/app/data`
4. 볼륨 생성 후 재배포

### 옵션 B: 외부 데이터베이스 사용

프로덕션 환경에서는 PostgreSQL이나 MySQL 같은 외부 데이터베이스 사용을 권장합니다.

## 4. 데이터베이스 초기화

첫 배포 시 데이터베이스가 비어있다면:

1. 로컬 `data/anime.db` 파일을 Railway 볼륨에 업로드하거나
2. 데이터베이스 마이그레이션 스크립트 실행

## 5. 배포 확인

배포 후 확인:

```bash
# Health check
curl https://your-backend.railway.app/health

# API 문서
# 브라우저에서: https://your-backend.railway.app/docs
```

## 6. Vercel 프론트엔드 연결

Vercel 프론트엔드 환경 변수에 Railway 백엔드 URL 추가:

```bash
VITE_API_BASE_URL=https://your-backend.railway.app
```

## 트러블슈팅

### 데이터베이스 파일을 찾을 수 없음
- 볼륨이 올바르게 마운트되었는지 확인
- DATABASE_PATH 환경 변수 확인

### CORS 에러
- PRODUCTION_ORIGIN이 정확한 Vercel URL인지 확인
- 프로토콜(https://)과 슬래시(/) 끝 제거 확인

### 이미지 로딩 안됨
- IMAGE_BASE_URL 설정 확인
- Cloudflare R2 버킷 퍼블릭 액세스 확인
