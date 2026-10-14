# AniBite

애니메이션·캐릭터를 평가하고 취향을 기록하는 소셜 서비스예요.

- 서비스: https://www.anibite.com
- API: https://api.anibite.com (`/health`, `/ready`)

## 기능

- 애니메이션·캐릭터 별점, 리뷰, 댓글, 좋아요
- 소셜 피드, 팔로우, 알림
- 오타쿠 레벨, 리더보드
- 작품·캐릭터 통합 검색, 연도·장르 필터
- Google 로그인 / 이메일 로그인
- **카탈로그 자동 업데이트**: 하루 한 번 AniList에서 이번·다음 시즌 인기작을 추가하고, 방영 중인 작품의 화수·상태·점수를 갱신해요. 한글 제목이 비어 있으면 AniList 한글 별칭으로 채워요. 사용자 데이터는 건드리지 않아요.

## 기술 구성

| 영역 | 구성 |
| --- | --- |
| 화면 | React 19, React Router 7, Vite, Tailwind CSS → Vercel |
| 서버 | FastAPI (Python 3.11), SQLite (Railway 볼륨 `/app/data`) → Railway (Dockerfile) |
| 이미지 | Cloudflare R2 (`images.anibite.com`), 없으면 AniList CDN |
| 데이터 원천 | AniList GraphQL |

## 로컬 실행 (macOS / Linux)

```bash
# 서버
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
export APP_ENV=development SECRET_KEY=$(python -c 'import secrets;print(secrets.token_hex(32))')
cd backend
DATABASE_PATH=../data/anime.db python migrations.py init   # 빈 DB 스키마 생성 (로컬 전용)
DATABASE_PATH=../data/anime.db uvicorn main:app --reload --port 8000

# 화면 (새 터미널)
cd frontend && npm ci && npm run dev
```

## 테스트

```bash
python -m pytest backend/tests -q        # 서버 (임시 DB만 사용)
cd frontend && npm run lint && npm test && npm run build && npm run test:e2e
```

## 운영 메모

- 카탈로그 동기화: 운영(`APP_ENV=production`)에서 서버 시작 10분 뒤부터 24시간 주기로 돌아요. 끄려면 `CATALOG_SYNC_ENABLED=0`. 마지막 실행 결과는 `GET /catalog-sync-status`.
- 수동 실행: `cd backend && python -m services.catalog_sync`
- 배포·마이그레이션 절차: [docs/refactor/DEPLOYMENT_RUNBOOK.md](docs/refactor/DEPLOYMENT_RUNBOOK.md)
- 백업: [docs/SAFE_BACKUPS.md](docs/SAFE_BACKUPS.md)
- **DB 파일(`*.db`)은 절대 커밋하지 않아요.** 사용자 정보가 들어 있어요.

예전 이름은 AniPass였고, 일부 내부 파일명(`MyAniPass.jsx` 등)에 남아 있어요.
