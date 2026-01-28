# CLAUDE.md - Anibite 프로젝트 컨텍스트

## 프로젝트 개요

**Anibite** - 애니메이션/캐릭터 평가 및 소셜 플랫폼

## 기술 스택

### 프론트엔드
- **프레임워크**: React + Vite
- **스타일링**: Tailwind CSS
- **배포**: Vercel
- **URL**: https://www.anibite.com

### 백엔드
- **프레임워크**: FastAPI (Python 3.11)
- **데이터베이스**: SQLite (`data/anime.db`)
- **이미지 저장소**: Cloudflare R2
- **배포**: Railway
- **URL**: https://api.anibite.com

## 프로젝트 구조

```
anibite/
├── frontend/           # React 프론트엔드
│   ├── src/
│   │   ├── components/ # 재사용 컴포넌트
│   │   ├── pages/      # 페이지 컴포넌트
│   │   ├── services/   # API 서비스
│   │   ├── context/    # React Context
│   │   └── hooks/      # Custom Hooks
│   └── vercel.json     # Vercel 설정
├── backend/            # FastAPI 백엔드
│   ├── api/            # API 라우터
│   ├── services/       # 비즈니스 로직
│   ├── models/         # Pydantic 모델
│   └── main.py         # 앱 진입점
├── data/               # 데이터베이스 및 스크립트
│   └── anime.db        # SQLite DB
├── railway.toml        # Railway 배포 설정
└── CLAUDE.md           # 이 파일
```

## 배포

### 프론트엔드 (Vercel)
- GitHub main 브랜치 푸시 시 자동 배포
- 대시보드: https://vercel.com

### 백엔드 (Railway)
- GitHub main 브랜치 푸시 시 자동 배포
- 대시보드: https://railway.app
- 볼륨 마운트: `/app/data` (DB 파일 저장)

## 주요 데이터베이스 테이블

| 테이블 | 설명 |
|--------|------|
| `anime` | 애니메이션 정보 |
| `character` | 캐릭터 정보 |
| `user_ratings` | 애니메이션 평점 (복수형 주의!) |
| `character_ratings` | 캐릭터 평점 (복수형 주의!) |
| `activities` | 사용자 활동 피드 |
| `follows` | 팔로우 관계 |

## API 엔드포인트 규칙

- 기본 URL: `https://api.anibite.com/api/`
- 인증: Bearer Token (JWT)

## 로컬 개발

### 백엔드 실행
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 실행
```bash
cd frontend
npm run dev
```

## 환경 변수

### 프론트엔드 (.env)
```
VITE_API_URL=https://api.anibite.com
VITE_IMAGE_BASE_URL=https://api.anibite.com
```

### 백엔드 (.env)
```
DATABASE_URL=sqlite:///data/anime.db
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_ENDPOINT=...
```

## 자주 사용하는 명령어

### Git 커밋 & 푸시 (자동 배포 트리거)
```bash
git add . && git commit -m "메시지" && git push
```

### 백엔드 재시작 (로컬)
```bash
# 기존 프로세스 종료
taskkill //F //IM python.exe
# 재시작
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 주의사항

1. **테이블명 복수형**: `user_ratings`, `character_ratings` (단수형 아님)
2. **이미지 URL**: R2 또는 로컬 경로 모두 지원, `IMAGE_BASE_URL` 사용
3. **CORS**: 백엔드에서 `www.anibite.com`, `anibite.com` 허용 필요
4. **배포 후 확인**: Railway 대시보드에서 배포 상태 확인

## 최근 변경사항

### 2025-01-29
- 통합 검색 API 추가 (`/api/search`) - 애니메이션 + 캐릭터 동시 검색
- 검색 페이지 실시간 검색 (디바운스 300ms)
- Navbar 반응형 개선 (600px 브레이크포인트)
- 피드 레이아웃 정렬 수정
