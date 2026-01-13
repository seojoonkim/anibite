# AniPass 데이터베이스 확장 계획

## Phase 1 (MVP) - 현재 구현
- ✅ 사용자 관리 (users, user_sessions)
- ✅ 애니메이션 종합 평점 (user_ratings: 0.5~5.0)
- ✅ 애니메이션 리뷰 (user_reviews)
- ✅ 리뷰 댓글 시스템 (review_comments) - **대댓글까지 2 depth**
- ✅ 댓글 좋아요 (comment_likes)
- ✅ 사용자 통계 (user_stats)
- ✅ 추천 캐시 (recommendation_cache)

---

## Phase 2 - 애니메이션 세부 평가

### 세부 항목 (5개)
1. **스토리** (story)
2. **캐릭터** (character)
3. **작화** (animation)
4. **음악** (music)
5. **연출** (direction)

### 추가 테이블

#### anime_aspect_ratings
```sql
CREATE TABLE anime_aspect_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    aspect TEXT NOT NULL CHECK(aspect IN ('story', 'character', 'animation', 'music', 'direction')),
    rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, anime_id, aspect)
);

CREATE INDEX idx_anime_aspect_ratings_user ON anime_aspect_ratings(user_id);
CREATE INDEX idx_anime_aspect_ratings_anime ON anime_aspect_ratings(anime_id);
CREATE INDEX idx_anime_aspect_ratings_aspect ON anime_aspect_ratings(aspect);
```

#### anime_aspect_reviews
```sql
CREATE TABLE anime_aspect_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    aspect TEXT NOT NULL CHECK(aspect IN ('story', 'character', 'animation', 'music', 'direction')),
    rating_id INTEGER REFERENCES anime_aspect_ratings(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    is_spoiler BOOLEAN DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, anime_id, aspect)
);

CREATE INDEX idx_anime_aspect_reviews_user ON anime_aspect_reviews(user_id);
CREATE INDEX idx_anime_aspect_reviews_anime ON anime_aspect_reviews(anime_id);
CREATE INDEX idx_anime_aspect_reviews_aspect ON anime_aspect_reviews(aspect);
```

### API 엔드포인트 (Phase 2)
```
POST   /api/ratings/aspect         - 세부 항목 평점
GET    /api/ratings/anime/{id}/aspects - 애니메이션 세부 평점 조회
POST   /api/reviews/aspect         - 세부 항목 리뷰
GET    /api/reviews/aspect/anime/{id}/{aspect} - 특정 항목 리뷰들
```

---

## Phase 3 - 캐릭터 평가 시스템

### 추가 테이블

#### character_ratings
```sql
CREATE TABLE character_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, character_id)
);

CREATE INDEX idx_character_ratings_user ON character_ratings(user_id);
CREATE INDEX idx_character_ratings_character ON character_ratings(character_id);
CREATE INDEX idx_character_ratings_rating ON character_ratings(rating DESC);
```

#### character_reviews
```sql
CREATE TABLE character_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    rating_id INTEGER REFERENCES character_ratings(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    is_spoiler BOOLEAN DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, character_id)
);

CREATE INDEX idx_character_reviews_user ON character_reviews(user_id);
CREATE INDEX idx_character_reviews_character ON character_reviews(character_id);
CREATE INDEX idx_character_reviews_likes ON character_reviews(likes_count DESC);
```

### API 엔드포인트 (Phase 3)
```
POST   /api/characters/{id}/rate   - 캐릭터 평점
POST   /api/characters/{id}/review - 캐릭터 리뷰
GET    /api/characters/{id}/reviews - 캐릭터 리뷰 목록
GET    /api/characters/top-rated   - 인기 캐릭터
```

---

## Phase 4 - 성우/스태프 평가 시스템

### 추가 테이블

#### staff_ratings
```sql
CREATE TABLE staff_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
    rating_context TEXT,  -- 'voice_acting', 'directing', 'writing' 등
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, staff_id)
);

CREATE INDEX idx_staff_ratings_user ON staff_ratings(user_id);
CREATE INDEX idx_staff_ratings_staff ON staff_ratings(staff_id);
CREATE INDEX idx_staff_ratings_rating ON staff_ratings(rating DESC);
```

#### staff_reviews
```sql
CREATE TABLE staff_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    rating_id INTEGER REFERENCES staff_ratings(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    is_spoiler BOOLEAN DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, staff_id)
);

CREATE INDEX idx_staff_reviews_user ON staff_reviews(user_id);
CREATE INDEX idx_staff_reviews_staff ON staff_reviews(staff_id);
CREATE INDEX idx_staff_reviews_likes ON staff_reviews(likes_count DESC);
```

### API 엔드포인트 (Phase 4)
```
POST   /api/staff/{id}/rate        - 성우/스태프 평점
POST   /api/staff/{id}/review      - 성우/스태프 리뷰
GET    /api/staff/{id}/reviews     - 성우/스태프 리뷰 목록
GET    /api/staff/top-rated        - 인기 성우/스태프
```

---

## 댓글 시스템 설계 (Phase 1에서 구현)

### 댓글 구조
- **1 depth**: 리뷰에 직접 달린 댓글
- **2 depth**: 댓글에 달린 대댓글 (최대 깊이)

### review_comments 테이블
```sql
CREATE TABLE review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_id INTEGER NOT NULL,  -- user_reviews.id
    review_type TEXT NOT NULL CHECK(review_type IN (
        'anime',           -- Phase 1
        'anime_aspect',    -- Phase 2
        'character',       -- Phase 3
        'staff'            -- Phase 4
    )) DEFAULT 'anime',
    parent_comment_id INTEGER REFERENCES review_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 대댓글 깊이 제한 (2 depth까지만)
    depth INTEGER DEFAULT 1 CHECK(depth IN (1, 2))
);

CREATE INDEX idx_review_comments_review ON review_comments(review_id, review_type);
CREATE INDEX idx_review_comments_user ON review_comments(user_id);
CREATE INDEX idx_review_comments_parent ON review_comments(parent_comment_id);
CREATE INDEX idx_review_comments_created ON review_comments(created_at DESC);

-- Trigger: 대댓글의 depth 자동 설정 및 검증
CREATE TRIGGER set_comment_depth
BEFORE INSERT ON review_comments
FOR EACH ROW
WHEN NEW.parent_comment_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN (SELECT depth FROM review_comments WHERE id = NEW.parent_comment_id) = 2
        THEN RAISE(ABORT, 'Cannot reply to a reply (max depth is 2)')
        ELSE 2
    END INTO NEW.depth;
END;
```

### comment_likes 테이블
```sql
CREATE TABLE comment_likes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment_id INTEGER NOT NULL REFERENCES review_comments(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, comment_id)
);

CREATE INDEX idx_comment_likes_comment ON comment_likes(comment_id);
```

### 댓글 API 엔드포인트 (Phase 1)
```
POST   /api/comments/                      - 댓글 작성
POST   /api/comments/{id}/reply            - 대댓글 작성
GET    /api/comments/review/{review_id}    - 리뷰의 댓글 목록
DELETE /api/comments/{id}                  - 댓글 삭제
POST   /api/comments/{id}/like             - 댓글 좋아요
DELETE /api/comments/{id}/like             - 댓글 좋아요 취소
```

---

## 확장 가능한 Backend 설계

### 서비스 레이어 구조
```
backend/services/
├── auth_service.py          # Phase 1
├── anime_service.py         # Phase 1
├── rating_service.py        # Phase 1 (확장 가능)
│   ├── rate_anime()
│   ├── rate_anime_aspect()      # Phase 2
│   ├── rate_character()         # Phase 3
│   └── rate_staff()             # Phase 4
├── review_service.py        # Phase 1 (확장 가능)
│   ├── create_anime_review()
│   ├── create_aspect_review()   # Phase 2
│   ├── create_character_review() # Phase 3
│   └── create_staff_review()    # Phase 4
├── comment_service.py       # Phase 1
│   ├── create_comment()
│   ├── create_reply()
│   ├── like_comment()
│   └── get_comments()
├── recommendation_service.py # Phase 3
└── profile_service.py       # Phase 2
```

### 공통 인터페이스 설계

```python
# rating_service.py
from enum import Enum

class RatingType(Enum):
    ANIME = "anime"
    ANIME_ASPECT = "anime_aspect"
    CHARACTER = "character"
    STAFF = "staff"

def create_rating(
    user_id: int,
    target_id: int,
    rating: float,
    rating_type: RatingType,
    aspect: str = None  # For anime_aspect
) -> dict:
    """범용 평점 생성 함수 - 모든 타입에 사용"""
    pass

def get_ratings(
    user_id: int,
    rating_type: RatingType,
    target_id: int = None
) -> list:
    """범용 평점 조회"""
    pass
```

---

## 마이그레이션 파일 목록

### 완료
- ✅ `001_add_user_tables.sql` - 기본 사용자 테이블

### Phase 1 추가
- `002_add_comment_system.sql` - 댓글 시스템

### Phase 2 (예정)
- `003_add_anime_aspect_ratings.sql` - 애니메이션 세부 평가

### Phase 3 (예정)
- `004_add_character_ratings.sql` - 캐릭터 평가

### Phase 4 (예정)
- `005_add_staff_ratings.sql` - 성우/스태프 평가

---

## Frontend 컴포넌트 확장 계획

### Phase 1
```
components/
├── comments/
│   ├── CommentList.jsx       # 댓글 목록
│   ├── CommentItem.jsx       # 댓글 아이템
│   ├── CommentForm.jsx       # 댓글 작성 폼
│   └── ReplyForm.jsx         # 대댓글 폼
```

### Phase 2
```
components/
├── rating/
│   ├── AspectRating.jsx      # 세부 항목 별점
│   ├── AspectRadarChart.jsx  # 5개 항목 레이더 차트
│   └── AspectBreakdown.jsx   # 세부 점수 분해
```

### Phase 3
```
components/
├── character/
│   ├── CharacterCard.jsx
│   ├── CharacterRating.jsx
│   └── CharacterReview.jsx
```

### Phase 4
```
components/
├── staff/
│   ├── StaffCard.jsx
│   ├── StaffRating.jsx
│   └── StaffReview.jsx
```

---

## 데이터 마이그레이션 전략

각 Phase 배포 시:
1. 새 테이블 추가 (기존 데이터 영향 없음)
2. 인덱스 생성
3. 기본값으로 초기화
4. 점진적으로 사용자가 데이터 입력

롤백 시:
- 테이블 삭제만 하면 됨 (기존 기능 영향 없음)

---

## 주의사항

1. **review_type 확장**: `review_comments` 테이블의 `review_type`이 처음부터 모든 타입 지원
2. **서비스 레이어 추상화**: 공통 로직을 재사용할 수 있도록 설계
3. **API 일관성**: 모든 평점/리뷰 API는 동일한 패턴 사용
4. **테스트**: 각 Phase 배포 전 기존 기능 회귀 테스트 필수

---

## 추천 알고리즘 확장 (Phase 3 이후)

### 기본 (Phase 3)
- 애니메이션 종합 평점 기반 Collaborative Filtering

### 확장 (Phase 4 이후)
- 세부 항목 가중치 적용
  - 사용자가 스토리를 중시 → 스토리 점수 높은 애니메이션 추천
- 캐릭터/성우 선호도 반영
  - 좋아하는 성우가 출연한 애니메이션 추천
  - 특정 캐릭터 타입 선호도 학습

---

## 성능 고려사항

### Phase 1
- 댓글 조회: `review_id` + `review_type` 복합 인덱스
- 대댓글 조회: `parent_comment_id` 인덱스

### Phase 2-4
- 각 평점 테이블에 적절한 인덱스
- 집계 쿼리 최적화 (평균 점수 계산)
- 캐싱 전략 (인기 캐릭터/성우 통계)

---

## 현재 상태
- ✅ Phase 1 DB 설계 완료
- ⏳ Phase 1 구현 시작 예정
- 📝 Phase 2-4 확장 계획 문서화 완료
