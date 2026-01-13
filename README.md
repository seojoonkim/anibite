# AniPass 🎬

애니메이션 평가 및 소셜 플랫폼

## 🚀 기능

- 애니메이션 평가 및 리뷰
- 캐릭터 평가
- 소셜 피드 (좋아요, 댓글, 팔로우)
- 알림 시스템
- 오타쿠 레벨 시스템
- 리더보드

## 🛠 기술 스택

### Frontend
- React 18
- React Router v6
- Tailwind CSS
- Vite

### Backend
- Python 3.x
- FastAPI
- SQLAlchemy
- SQLite

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/anipass.git
cd anipass
```

### 2. Backend 설정
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend 설정
```bash
cd frontend
npm install
npm run dev
```

### 4. 브라우저에서 접속
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## 📁 프로젝트 구조

```
anipass/
├── frontend/          # React 앱
├── backend/           # FastAPI 서버
├── data/
│   ├── anime.db      # SQLite 데이터베이스
│   └── images/       # 이미지 파일 (로컬 개발용)
└── docs/             # 문서
```

## 🖼 이미지 설정

### 개발 환경
이미지는 로컬 `data/images/` 디렉토리에서 제공됩니다.

### 프로덕션 환경
이미지는 Cloudflare R2에 호스팅됩니다. `.env` 파일에 설정:

```bash
IMAGE_BASE_URL=https://your-bucket.r2.dev/images
```

## 📝 라이선스

MIT

## 🤝 기여

이슈와 PR을 환영합니다!
