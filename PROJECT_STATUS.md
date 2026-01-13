# AniPass - 애니메이션 평가 플랫폼 프로젝트 현황

**마지막 업데이트:** 2026-01-12
**프로젝트 타입:** 왓챠피디아 스타일의 애니메이션 평가/리뷰 플랫폼

---

## 📋 프로젝트 개요

AniPass는 애니메이션 애호가들을 위한 종합 평가 및 소셜 플랫폼입니다.
- 3,000개 이상의 애니메이션 데이터
- 사용자 평점/리뷰 시스템
- 캐릭터 평가 기능
- 소셜 피드 기능
- 오타쿠 레벨 시스템

---

## 🛠 기술 스택

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Database:** SQLite (anime.db)
- **Authentication:** JWT
- **Server:** Uvicorn (http://localhost:8000)

### Frontend
- **Framework:** React (Vite)
- **Router:** React Router v6
- **Styling:** Tailwind CSS
- **State:** React Context API
- **Server:** Vite Dev Server (http://localhost:5174)

### Data
- **Source:** AniList API
- **Images:** 로컬 저장 (/data/images/)
- **Total Anime:** ~3,000작품
- **Characters:** ~16,885개
- **Staff:** ~6,957명

---

## 📊 데이터베이스 구조

### 주요 테이블

**users** - 사용자 계정
```sql
- id, username, email, password_hash
- display_name, avatar_url
- created_at
```

**user_stats** - 사용자 통계
```sql
- user_id, otaku_score
- total_rated, total_reviews
- average_rating, favorite_genre
```

**anime** - 애니메이션 정보
```sql
- id, title_romaji, title_korean, title_english
- cover_image_url, description
- status, format, episodes, duration
- season, season_year, genres, studios
```

**user_ratings** - 평점
```sql
- id, user_id, anime_id
- rating (0.5~5.0 단위), status
- created_at, updated_at
```

**user_reviews** - 리뷰
```sql
- id, user_id, anime_id, rating_id
- content, is_spoiler
- likes_count, comments_count
```

**character** - 캐릭터 정보
```sql
- id, name_full, name_native
- image_url, description
- gender, age, date_of_birth
```

**character_ratings** - 캐릭터 평가
```sql
- id, user_id, character_id
- rating, comment
```

**review_comments** - 리뷰 댓글
```sql
- id, user_id, review_id, review_type
- content, parent_comment_id
- likes_count
```

**activity_likes** - 활동 좋아요
```sql
- activity_type, activity_user_id, item_id
- liker_user_id, created_at
```

**activity_comments** - 활동 댓글
```sql
- activity_type, activity_user_id, item_id
- commenter_user_id, content
```

**user_follows** - 팔로우
```sql
- follower_user_id, following_user_id
```

**notifications** - 알림
```sql
- user_id, type, actor_user_id
- activity_type, item_id
- is_read, created_at
```

---

## 🎯 주요 기능

### 1. 인증 시스템 ✅
- JWT 기반 로그인/회원가입
- 프로필 이미지 업로드
- 사용자 통계 자동 계산

### 2. 애니메이션 평가 ✅
- 0.5~5.0 별점 평가
- 보고싶어요/패스 마킹
- 사이트 평균 평점 표시
- 평점 분포 히스토그램

### 3. 리뷰 시스템 ✅
- 리뷰 작성/수정/삭제
- 스포일러 태그
- 리뷰 좋아요
- 리뷰 댓글 (2단계: 댓글 + 답글)
- 댓글 좋아요

### 4. 캐릭터 시스템 ✅
- 캐릭터 상세 정보
- 캐릭터 평가 (별점 + 코멘트)
- 캐릭터-성우 연결
- 캐릭터별 출연작 목록

### 5. 소셜 피드 ✅
- 전체/팔로잉/알림/저장 필터
- 평가/리뷰 활동 표시
- 좋아요/댓글 기능
- 활동 저장 기능
- URL 파라미터로 상태 유지

### 6. 오타쿠 레벨 시스템 ✅
- 10단계 레벨: 루키 → 오타쿠 갓
- 점수 계산: 평가수, 리뷰수, 시청시간 기반
- 프로필 뱃지 표시 (아이콘 + 레벨명 + 로마숫자)

### 7. 알림 시스템 ✅
- 좋아요 알림 (그룹화)
- 댓글 알림 (그룹화)
- 팔로우 알림
- 실시간 알림 수 표시

### 8. 팔로우 시스템 ✅
- 사용자 팔로우/언팔로우
- 팔로워/팔로잉 목록
- 팔로잉 필터 피드

### 9. 검색 기능 ✅
- 애니메이션 검색
- 장르/연도/상태 필터
- 정렬 옵션 (평점, 제목, 연도)
- 랜덤 인기 작품 플레이스홀더

---

## 📁 프로젝트 구조

```
anipass/
├── backend/
│   ├── main.py                 # FastAPI 앱
│   ├── database.py            # DB 연결
│   ├── api/                   # API 라우터
│   │   ├── auth.py
│   │   ├── anime.py
│   │   ├── ratings.py
│   │   ├── reviews.py
│   │   ├── characters.py
│   │   ├── comments.py
│   │   ├── feed.py
│   │   ├── notifications.py
│   │   ├── follows.py
│   │   └── users.py
│   ├── services/              # 비즈니스 로직
│   │   ├── auth_service.py
│   │   ├── anime_service.py
│   │   ├── rating_service.py
│   │   ├── review_service.py
│   │   ├── character_service.py
│   │   ├── comment_service.py
│   │   └── feed_service.py
│   └── models/                # Pydantic 모델
│       ├── user.py
│       ├── rating.py
│       ├── review.py
│       └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx           # 애니메이션 목록
│   │   │   ├── AnimeDetail.jsx    # 작품 상세
│   │   │   ├── CharacterDetail.jsx # 캐릭터 상세
│   │   │   ├── Feed.jsx           # 소셜 피드
│   │   │   ├── Profile.jsx        # 사용자 프로필
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Navbar.jsx
│   │   │   │   └── StarRating.jsx
│   │   │   └── anime/
│   │   │       ├── AnimeCard.jsx
│   │   │       └── RatingWidget.jsx
│   │   ├── services/          # API 호출
│   │   │   ├── animeService.js
│   │   │   ├── ratingService.js
│   │   │   ├── reviewService.js
│   │   │   ├── reviewLikeService.js
│   │   │   ├── reviewCommentService.js
│   │   │   └── ...
│   │   ├── context/
│   │   │   ├── AuthContext.jsx
│   │   │   └── LanguageContext.jsx
│   │   └── utils/
│   │       └── otakuLevels.js  # 레벨 시스템
│   └── package.json
├── data/
│   ├── anime.db               # SQLite 데이터베이스
│   ├── schema.sql            # DB 스키마
│   ├── images/               # 이미지 저장소
│   │   ├── anime/
│   │   ├── characters/
│   │   └── staff/
│   └── download_images.py    # 이미지 다운로드 스크립트
└── PROJECT_STATUS.md         # 이 파일
```

---

## 🔄 최근 작업 내용

### 2026-01-12 - 좋아요/저장 기능 버그 수정 ⭐

**문제:**
1. ❌ 좋아요를 누르면 review_likes 테이블에는 추가되지만 user_reviews.likes_count가 업데이트 안 됨
2. ❌ 좋아요 취소 시에도 likes_count 업데이트 안 됨
3. ❌ 저장하기 버튼이 작동하지 않음 (클릭 핸들러 없음)
4. ❌ 저장된 리뷰에 "1" 숫자가 표시 안 됨

**원인 분석:**
- 백엔드: `like_review()`, `unlike_review()` 함수가 review_likes 테이블만 수정하고 user_reviews.likes_count 필드를 업데이트하지 않음
- 프론트엔드: savedReviews 상태는 선언되었지만 초기화 및 핸들러 미구현

**해결:**

#### 백엔드 수정 (backend/services/review_service.py)

1. **like_review() 함수** (lines 340-352):
   ```python
   # 좋아요 추가
   db.execute_insert(
       "INSERT INTO review_likes (user_id, review_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
       (user_id, review_id)
   )

   # likes_count 업데이트 추가 ⭐
   db.execute_update(
       "UPDATE user_reviews SET likes_count = likes_count + 1 WHERE id = ?",
       (review_id,)
   )
   ```

2. **unlike_review() 함수** (lines 355-375):
   ```python
   # 좋아요 삭제
   rowcount = db.execute_update(
       "DELETE FROM review_likes WHERE user_id = ? AND review_id = ?",
       (user_id, review_id)
   )

   # likes_count 업데이트 추가 (0 미만 방지) ⭐
   db.execute_update(
       "UPDATE user_reviews SET likes_count = CASE WHEN likes_count > 0 THEN likes_count - 1 ELSE 0 END WHERE id = ?",
       (review_id,)
   )
   ```

#### 프론트엔드 수정 (frontend/src/pages/AnimeDetail.jsx)

1. **localStorage 초기화** (lines 56-62):
   ```javascript
   // 컴포넌트 마운트 시 저장된 리뷰 로드
   useEffect(() => {
     const saved = localStorage.getItem('savedReviews');
     if (saved) {
       setSavedReviews(new Set(JSON.parse(saved)));
     }
   }, []);
   ```

2. **저장 토글 핸들러** (lines 261-273):
   ```javascript
   const handleToggleSaveReview = (reviewId) => {
     setSavedReviews(prev => {
       const newSet = new Set(prev);
       if (newSet.has(reviewId)) {
         newSet.delete(reviewId);
       } else {
         newSet.add(reviewId);
       }
       // 로컬 스토리지에 저장
       localStorage.setItem('savedReviews', JSON.stringify([...newSet]));
       return newSet;
     });
   };
   ```

3. **저장 버튼 구현** (lines 1082-1102):
   ```javascript
   <button
     onClick={() => handleToggleSaveReview(review.id)}
     className="flex items-center gap-2 transition-all hover:scale-110"
     style={{
       color: savedReviews.has(review.id) ? '#3FC1C9' : '#6B7280'
     }}
   >
     {savedReviews.has(review.id) ? (
       // 저장됨: 채워진 북마크 아이콘
       <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
         <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
       </svg>
     ) : (
       // 미저장: 빈 북마크 아이콘
       <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
         <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
       </svg>
     )}
     {savedReviews.has(review.id) && (
       <span className="text-sm font-medium">1</span>
     )}
   </button>
   ```

**테스트 데이터 생성:**
```sql
-- 테스트용 사용자 추가
INSERT INTO users (username, email, password_hash, display_name)
VALUES ('testuser2', 'test2@example.com', 'hash', 'Test User 2');

-- 리뷰에 좋아요 추가 (수동)
INSERT INTO review_likes (user_id, review_id) VALUES (5, 3);
UPDATE user_reviews SET likes_count = likes_count + 1 WHERE id = 3;

-- 리뷰에 댓글 추가 (수동)
INSERT INTO review_comments (user_id, review_id, review_type, content)
VALUES (5, 3, 'anime', 'This is a test comment!');
```

**결과:**
- ✅ 좋아요/좋아요 취소 시 likes_count가 올바르게 증가/감소
- ✅ 저장 버튼 클릭 시 상태 토글 (채워진/빈 북마크)
- ✅ 저장된 리뷰에 "1" 표시
- ✅ 새로고침 후에도 저장 상태 유지 (localStorage)
- ✅ Feed.jsx와 동일한 동작 방식

**영향받는 파일:**
- `/backend/services/review_service.py`
- `/frontend/src/pages/AnimeDetail.jsx`

---

### 2026-01-11 오후 - 작품 상세 페이지 리뷰 버그 수정

**문제:**
1. ❌ 프로필 이미지가 안 나옴
2. ❌ 별점평이 안 나옴
3. ❌ 좋아요 정보가 안 나옴 (숫자 0으로 표시)
4. ❌ 댓글 정보가 안 나옴 (숫자 0으로 표시)
5. ❌ 댓글이 이미 있으면 펼쳐져서 나와야 하는데 안 됨
6. ❌ 저장하기 아이콘이 없음

**원인:**
- 백엔드: ReviewResponse 모델에 필수 필드 누락
  - `display_name`, `comments_count`, `user_liked`, `otaku_score` 없음
- 프론트엔드: 잘못된 필드명 사용
  - `review.avatar_url` → 실제는 `review.user_avatar`
  - `review.rating` → 실제는 `review.user_rating`

**해결:**

#### 백엔드 수정
`/backend/models/review.py` - ReviewResponse 모델에 필드 추가:
```python
display_name: Optional[str] = None
comments_count: Optional[int] = 0
user_liked: Optional[bool] = False
otaku_score: Optional[float] = 0
```

#### 프론트엔드 수정
`/frontend/src/pages/AnimeDetail.jsx`:
1. 필드명 수정:
   - `review.avatar_url` → `review.user_avatar`
   - `review.rating` → `review.user_rating`
2. likeInfo 초기화 개선:
   ```javascript
   const likeInfo = reviewLikes[review.id] || {
     liked: review.user_liked || false,
     count: review.likes_count || 0
   };
   ```
3. 저장하기 아이콘 추가 (북마크 아이콘)

**결과:** ✅ 모든 정보가 올바르게 표시됨

---

### 2026-01-11 오전

### 1. Feed URL 파라미터 추가
- 각 메뉴(전체/팔로잉/알림/저장)에 URL 할당
- 새로고침 시 현재 메뉴 유지
- `/feed?filter=all`, `/feed?filter=following` 등

### 2. 저장 기능 UI 개선
- 저장된 항목에만 "1" 표시
- 전체 개수 제거

### 3. 알림 시스템 확장
- 캐릭터 평가 활동 알림 지원
- 캐릭터 썸네일 표시
- 테이블명 수정 (characters → character)

### 4. 검색 UI 개선
- 인기 작품 50개 중 랜덤 1개를 플레이스홀더로 표시
- 페이지 로드 시 자동 설정

### 5. 리뷰 시스템 대대적 개선 ⭐
**작품 상세 페이지 리뷰를 피드와 동일한 형식으로 통일:**

#### 백엔드 변경
- `user_stats` JOIN 추가
- `otaku_score`, `display_name` 포함
- `comments_count`, `user_liked` 추가
- 테이블명 수정 (comments → review_comments)

#### 프론트엔드 변경
- **레이아웃 변경:**
  - 왼쪽: 작품 이미지 (16×24)
  - 오른쪽: 콘텐츠 영역
- **헤더:**
  - 프로필 이미지 (8×8) + 이름 + 뱃지 + "작품을 평가했어요" + 시간
  - 오른쪽 상단: ... 메뉴 (수정/삭제)
- **내용:**
  - 작품 제목
  - 별점
  - 리뷰 내용
  - 좋아요/댓글 달기 버튼 (아이콘 + 텍스트)
- **상호작용:**
  - 좋아요 토글 (채워진 하트 ↔ 빈 하트)
  - 댓글 펼치기/접기
  - 댓글 작성 (Enter 키 지원)
  - 답글 작성
  - 댓글/답글 좋아요
  - 댓글/답글 삭제 (본인만)
- **서비스 파일 추가:**
  - `reviewLikeService.js`
  - `reviewCommentService.js`

### 6. 이미지 다운로드 작업
- 백그라운드에서 캐릭터/성우 이미지 다운로드 진행 중
- 예상 완료 시간: ~85분
- 현재 진행률: 진행 중

---

## 🎨 UI/UX 특징

### 색상 테마
- Primary: `#3FC1C9` (청록색)
- Secondary: `#364F6B` (남색)
- 배경: `#F3F4F6` (연한 회색)
- 텍스트: `#1F2937` (진한 회색)

### 오타쿠 레벨 뱃지
```
🌱 루키 - I        (0-49점)
🎯 헌터 - II       (50-119점)
⚔️ 워리어 - III     (120-219점)
🛡️ 나이트 - IV      (220-349점)
⭐ 마스터 - V       (350-549점)
✨ 하이마스터 - VI   (550-799점)
👑 그랜드마스터 - VII (800-1099점)
📺 오타쿠 - VIII    (1100-1449점)
🏆 오타쿠 킹 - IX   (1450-1799점)
💎 오타쿠 갓 - X    (1800+점)
```

### 반응형 디자인
- 모바일: 2열 그리드
- 태블릿: 3-4열 그리드
- 데스크톱: 6열 그리드
- 네비게이션: 모바일에서 하단 고정

---

## 📝 남은 작업

### 우선순위 높음
- [ ] 추천 시스템 (Collaborative Filtering)
  - 유사 사용자 찾기
  - 평점 예측
  - 추천 캐싱
- [ ] 프로필 페이지 완성
  - 평점 히스토리
  - 장르 선호도 차트
  - 시청 시간 통계
- [ ] 시리즈 기능
  - 시리즈 그룹핑
  - 시리즈 목록 보기

### 우선순위 중간
- [ ] 이미지 최적화
  - Lazy loading
  - Placeholder 이미지
  - CDN 고려
- [ ] 검색 개선
  - 자동완성
  - 고급 필터
- [ ] 리뷰 정렬 옵션
  - 최신순, 좋아요순, 평점순

### 우선순위 낮음
- [ ] 다크 모드
- [ ] 리뷰 신고 기능
- [ ] 사용자 차단
- [ ] 리뷰 스포일러 필터
- [ ] 애니메이션 위시리스트 공유

---

## 🔧 개발 환경 설정

### 백엔드 실행
```bash
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```

### 이미지 다운로드
```bash
cd data
python3 download_images.py
```

---

## 🐛 알려진 이슈

### 해결됨
- ✅ 저장 버튼에 전체 개수 표시 → 저장된 항목만 "1" 표시
- ✅ 알림에서 캐릭터 썸네일 안 보임 → 테이블명 수정
- ✅ 작품 상세 페이지 리뷰 형식 불일치 → 피드와 동일하게 통일
- ✅ 리뷰 댓글 기능 없음 → 전체 구현 완료

### 진행 중
- 🔄 이미지 다운로드 작업 (백그라운드)

### 미해결
- 없음

---

## 📊 데이터 현황

- **애니메이션:** ~3,000개
- **캐릭터:** 16,885개
- **성우:** 6,957명
- **다운로드된 이미지:** 진행 중

---

## 🎯 다음 단계

1. **추천 시스템 구현**
   - User-User Collaborative Filtering
   - Pearson Correlation 기반
   - Cold Start 해결 (인기/트렌딩)

2. **프로필 페이지 강화**
   - 시청 통계 차트
   - 장르 선호도 분석
   - 평점 히스토리 타임라인

3. **성능 최적화**
   - 이미지 Lazy Loading
   - API 응답 캐싱
   - 쿼리 최적화

4. **사용자 경험 개선**
   - 로딩 스켈레톤
   - 에러 핸들링
   - 토스트 알림

---

## 💡 참고사항

- 모든 시간은 상대 시간으로 표시 (방금 전, 5분 전, 2시간 전 등)
- 이미지 로드 실패 시 자동 fallback
- JWT 토큰은 localStorage에 저장
- 언어: 한국어/영어 지원
- 모든 API는 `/api/` prefix 사용

---

**작성자:** Claude Code
**프로젝트 시작:** 2025년
**현재 버전:** MVP (Phase 1-2 완료)
