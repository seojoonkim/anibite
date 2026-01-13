# AniPass Backend API

왓챠피디아 스타일 애니메이션 평가 플랫폼 Backend (FastAPI)

## 설치

```bash
cd backend
pip install -r requirements.txt
```

## 실행

```bash
python main.py
# 또는
uvicorn main:app --reload --port 8000
```

## API 문서

서버 실행 후:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## ✅ 구현된 API (Phase 1)

### Authentication (`/api/auth`)
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인 (JWT 토큰 발급)
- `GET /api/auth/me` - 현재 사용자 정보

### Anime (`/api/anime`)
- `GET /api/anime/` - 애니메이션 목록 (필터링, 페이지네이션)
- `GET /api/anime/{id}` - 애니메이션 상세 정보
- `GET /api/anime/search` - 제목 검색
- `GET /api/anime/popular` - 인기 애니메이션
- `GET /api/anime/top-rated` - 최고 평점 애니메이션
- `GET /api/anime/genres` - 장르 목록

### Ratings (`/api/ratings`)
- `POST /api/ratings/` - 평점 생성/수정 (0.5~5.0, 0.5 단위)
- `GET /api/ratings/me` - 내 평점 목록
- `GET /api/ratings/anime/{id}` - 특정 애니메이션에 대한 내 평점
- `DELETE /api/ratings/anime/{id}` - 평점 삭제

### Reviews (`/api/reviews`)
- `POST /api/reviews/` - 리뷰 작성
- `PUT /api/reviews/{id}` - 리뷰 수정
- `DELETE /api/reviews/{id}` - 리뷰 삭제
- `GET /api/reviews/{id}` - 리뷰 상세
- `GET /api/reviews/anime/{id}` - 애니메이션의 리뷰 목록
- `GET /api/reviews/user/{id}` - 사용자의 리뷰 목록
- `POST /api/reviews/{id}/like` - 리뷰 좋아요
- `DELETE /api/reviews/{id}/like` - 리뷰 좋아요 취소

### Comments (`/api/comments`)
- `POST /api/comments/` - 댓글 작성 (1 depth)
- `POST /api/comments/{id}/reply` - 대댓글 작성 (2 depth)
- `DELETE /api/comments/{id}` - 댓글 삭제
- `GET /api/comments/review/{id}` - 리뷰의 댓글 목록
- `POST /api/comments/{id}/like` - 댓글 좋아요
- `DELETE /api/comments/{id}/like` - 댓글 좋아요 취소

### Users (`/api/users`)
- `GET /api/users/me/profile` - 내 프로필 (정보 + 통계)
- `GET /api/users/me/stats` - 내 통계 (오타쿠 점수, 평가 수, 시청 시간)
- `GET /api/users/me/genre-preferences` - 내 장르 선호도
- `GET /api/users/me/rating-distribution` - 내 평점 분포
- `GET /api/users/me/watch-history` - 최근 평가한 애니메이션
- `GET /api/users/{id}/profile` - 다른 사용자 프로필 (공개)
- `GET /api/users/{id}/genre-preferences` - 다른 사용자 장르 선호도

## 데이터베이스

- **SQLite**: `../data/anime.db`
- **애니메이션**: 3,000개
- **마이그레이션**: `../data/migrations/`
  - `001_add_user_tables.sql` - 사용자 테이블
  - `002_add_comment_system.sql` - 댓글 시스템

## 인증

JWT Bearer Token 방식
- 헤더: `Authorization: Bearer <token>`
- 토큰 유효기간: 7일

## 프로젝트 구조

```
backend/
├── main.py              # FastAPI 앱
├── config.py            # 설정
├── database.py          # DB 연결
├── requirements.txt     # 의존성
├── models/              # Pydantic 모델
│   ├── user.py
│   ├── anime.py
│   ├── rating.py
│   ├── review.py
│   └── comment.py
├── api/                 # API 라우터
│   ├── deps.py         # 의존성 (인증)
│   ├── auth.py
│   ├── anime.py
│   ├── ratings.py
│   ├── reviews.py
│   ├── comments.py
│   └── users.py
├── services/            # 비즈니스 로직
│   ├── auth_service.py
│   ├── anime_service.py
│   ├── rating_service.py
│   ├── review_service.py
│   ├── comment_service.py
│   └── profile_service.py
└── utils/               # 유틸리티
    └── security.py     # JWT, 비밀번호 해싱
```

## Phase 2-4 확장 계획

확장 계획 문서: `../docs/DATABASE_EXPANSION_PLAN.md`

- **Phase 2**: 애니메이션 세부 평가 (스토리, 캐릭터, 작화, 음악, 연출)
- **Phase 3**: 캐릭터 평가 시스템
- **Phase 4**: 성우/스태프 평가 시스템
