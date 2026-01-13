# AniPass 리팩토링 계획: 통합 활동 시스템

## 현재 문제점

### 1. 데이터베이스 중복
```
활동 저장:
- user_ratings (애니 평점)
- character_ratings (캐릭터 평점)
- user_reviews (애니 리뷰)
- character_reviews (캐릭터 리뷰)
- feed_activities (피드용 denormalized)

좋아요 저장:
- activity_likes (활동 좋아요)
- review_likes (리뷰 좋아요)
- character_review_likes (캐릭터 리뷰 좋아요)

댓글 저장:
- activity_comments (활동 댓글)
- review_comments (리뷰 댓글)
```

**결과**: 같은 데이터가 여러 테이블에 흩어져 있어서 불일치 발생

### 2. 프론트엔드 중복
- `Feed.jsx` - 피드 아이템 렌더링
- `AnimeDetail.jsx` - 애니 리뷰 렌더링
- `CharacterDetail.jsx` - 캐릭터 리뷰 렌더링
- `MyAniPass.jsx` - 내 활동 렌더링

**결과**:
- 각 페이지마다 다른 방식으로 구현
- 아바타가 어떤 페이지에서는 보이고 어떤 페이지에서는 안보임
- 좋아요/댓글 로직이 페이지마다 다름

### 3. 백엔드 API 분산
- `/api/reviews/` - 애니 리뷰
- `/api/character-reviews/` - 캐릭터 리뷰
- `/api/feed/` - 피드
- `/api/users/{id}/ratings` - 사용자 평점
- `/api/users/{id}/character-ratings` - 사용자 캐릭터 평점

**결과**: 같은 활동을 다른 엔드포인트에서 다르게 조회

---

## 리팩토링 목표

### 핵심 개념: "Activity" 통합 모델

**모든 사용자 활동은 동일한 구조로 저장/조회/렌더링**

```
Activity Types:
1. anime_rating - 애니 평점 (+ 선택적 리뷰)
2. character_rating - 캐릭터 평점 (+ 선택적 리뷰)
3. user_post - 일반 게시글
```

---

## Phase 1: 데이터베이스 통합

### 1.1 활동 테이블 (feed_activities 확장)

**현재**: feed_activities는 피드용으로만 사용
**목표**: 모든 활동의 단일 소스

```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 활동 타입
    activity_type TEXT NOT NULL, -- 'anime_rating', 'character_rating', 'user_post'

    -- 주체
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    otaku_score INTEGER DEFAULT 0,

    -- 대상 (item)
    item_id INTEGER, -- anime_id or character_id or NULL (for posts)
    item_title TEXT,
    item_title_korean TEXT,
    item_image TEXT,

    -- 평점 & 리뷰
    rating REAL, -- 0.5 ~ 5.0 or NULL
    review_title TEXT,
    review_content TEXT,
    is_spoiler BOOLEAN DEFAULT 0,

    -- 메타데이터 (캐릭터용)
    anime_id INTEGER, -- character의 대표 애니
    anime_title TEXT,
    anime_title_korean TEXT,

    -- 타임스탬프
    activity_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 인덱스
    UNIQUE(activity_type, user_id, item_id)
);

CREATE INDEX idx_activities_user ON activities(user_id, activity_time DESC);
CREATE INDEX idx_activities_item ON activities(activity_type, item_id, activity_time DESC);
CREATE INDEX idx_activities_time ON activities(activity_time DESC);
```

### 1.2 좋아요 테이블 통합

**제거**: `review_likes`, `character_review_likes`
**유지**: `activity_likes` (단일 테이블)

```sql
CREATE TABLE activity_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL, -- activities.id 참조
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, activity_id)
);

CREATE INDEX idx_activity_likes_activity ON activity_likes(activity_id);
CREATE INDEX idx_activity_likes_user ON activity_likes(user_id);
```

### 1.3 댓글 테이블 통합

**제거**: `review_comments`
**유지**: `activity_comments` (확장)

```sql
CREATE TABLE activity_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL, -- activities.id 참조
    user_id INTEGER NOT NULL,
    parent_comment_id INTEGER, -- 대댓글용
    content TEXT NOT NULL,
    depth INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_comments_activity ON activity_comments(activity_id, created_at);
CREATE INDEX idx_activity_comments_parent ON activity_comments(parent_comment_id);
```

### 1.4 원본 테이블 유지 (데이터 무결성용)

**유지하되 단순화**:
- `user_ratings` - 평점 원본 (통계용)
- `character_ratings` - 캐릭터 평점 원본 (통계용)

**제거**:
- `user_reviews` - activities에 통합
- `character_reviews` - activities에 통합
- `feed_activities` - activities로 이름 변경

---

## Phase 2: 백엔드 API 통합

### 2.1 단일 Activities 엔드포인트

```python
# /api/activities/
@router.get("/")
def get_activities(
    activity_type: Optional[str] = None,  # 'anime_rating', 'character_rating', 'user_post'
    user_id: Optional[int] = None,        # 특정 사용자 활동
    item_id: Optional[int] = None,        # 특정 아이템의 활동들
    following_only: bool = False,          # 팔로잉 피드
    limit: int = 50,
    offset: int = 0
) -> List[ActivityResponse]:
    """통합 활동 조회"""
    pass
```

### 2.2 표준화된 응답 형식

```python
class ActivityResponse(BaseModel):
    # Activity core
    id: int
    activity_type: str
    user_id: int

    # User info (denormalized)
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    otaku_score: int

    # Item info (denormalized)
    item_id: Optional[int]
    item_title: Optional[str]
    item_title_korean: Optional[str]
    item_image: Optional[str]

    # Rating & Review
    rating: Optional[float]
    review_title: Optional[str]
    review_content: Optional[str]
    is_spoiler: bool

    # Metadata
    anime_id: Optional[int]  # for characters
    anime_title: Optional[str]
    anime_title_korean: Optional[str]

    # Engagement
    likes_count: int
    comments_count: int
    user_liked: bool  # if current_user liked this

    # Timestamps
    activity_time: datetime
    created_at: datetime
    updated_at: datetime
```

### 2.3 마이그레이션 전략

1. **기존 API 유지** (호환성)
   - `/api/reviews/` → activities로 프록시
   - `/api/character-reviews/` → activities로 프록시

2. **새 API 점진적 도입**
   - 프론트엔드를 페이지별로 마이그레이션
   - 완료 후 구 API 제거

---

## Phase 3: 프론트엔드 통합

### 3.1 ActivityCard 컴포넌트 생성

**위치**: `/frontend/src/components/activity/ActivityCard.jsx`

```jsx
/**
 * 통합 활동 카드 컴포넌트
 *
 * 사용 예:
 * <ActivityCard
 *   activity={activity}
 *   context="feed"
 *   onUpdate={refetch}
 * />
 */
export default function ActivityCard({ activity, context, onUpdate }) {
  // context: 'feed', 'anime_page', 'character_page', 'profile', 'notification'

  return (
    <div className="activity-card">
      {/* 사용자 정보 헤더 */}
      <ActivityHeader activity={activity} />

      {/* 아이템 이미지 (context에 따라 표시 여부 결정) */}
      {shouldShowItemImage(context) && (
        <ActivityItemImage activity={activity} />
      )}

      {/* 평점 */}
      {activity.rating && <ActivityRating rating={activity.rating} />}

      {/* 리뷰 내용 */}
      {activity.review_content && (
        <ActivityReview content={activity.review_content} isSpoiler={activity.is_spoiler} />
      )}

      {/* 좋아요/댓글 버튼 */}
      <ActivityActions
        activity={activity}
        onLike={handleLike}
        onComment={toggleComments}
      />

      {/* 댓글 섹션 */}
      {showComments && (
        <ActivityComments activityId={activity.id} />
      )}
    </div>
  );
}
```

### 3.2 하위 컴포넌트 구조

```
/components/activity/
  ├── ActivityCard.jsx          # 메인 카드
  ├── ActivityHeader.jsx         # 사용자 정보 + 아바타
  ├── ActivityItemImage.jsx      # 애니/캐릭터 이미지
  ├── ActivityRating.jsx         # 별점 표시
  ├── ActivityReview.jsx         # 리뷰 내용
  ├── ActivityActions.jsx        # 좋아요/댓글/저장 버튼
  ├── ActivityComments.jsx       # 댓글 섹션
  └── activityHelpers.js         # 유틸리티 함수
```

### 3.3 페이지별 적용

```jsx
// Feed.jsx
import ActivityCard from '@/components/activity/ActivityCard';

function Feed() {
  const { data: activities } = useActivities({ following_only: true });

  return (
    <div>
      {activities.map(activity => (
        <ActivityCard
          key={activity.id}
          activity={activity}
          context="feed"
        />
      ))}
    </div>
  );
}

// AnimeDetail.jsx
function AnimeDetail() {
  const { id } = useParams();
  const { data: activities } = useActivities({
    activity_type: 'anime_rating',
    item_id: id
  });

  return (
    <div>
      {activities.map(activity => (
        <ActivityCard
          key={activity.id}
          activity={activity}
          context="anime_page" // 아이템 이미지 숨김
        />
      ))}
    </div>
  );
}

// CharacterDetail.jsx - 동일한 패턴
// MyAniPass.jsx - 동일한 패턴
```

### 3.4 Context 기반 조건부 렌더링

```javascript
// activityHelpers.js
export const shouldShowItemImage = (context) => {
  // 피드와 프로필에서는 아이템 이미지 표시
  // 애니/캐릭터 페이지에서는 숨김 (이미 페이지 헤더에 있음)
  return ['feed', 'profile', 'notification'].includes(context);
};

export const shouldShowDeleteButton = (activity, currentUser, context) => {
  return activity.user_id === currentUser?.id;
};

export const getActivityLink = (activity) => {
  if (activity.activity_type === 'anime_rating') {
    return `/anime/${activity.item_id}`;
  } else if (activity.activity_type === 'character_rating') {
    return `/character/${activity.item_id}`;
  }
  return null;
};
```

---

## Phase 4: 서비스 레이어 통합

### 4.1 프론트엔드 서비스 통합

**제거할 서비스**:
- `reviewService.js`
- `characterReviewService.js`
- `reviewLikeService.js`
- (일부 중복 기능)

**통합 서비스**:

```javascript
// activityService.js
export const activityService = {
  // 활동 조회
  async getActivities({ activityType, userId, itemId, followingOnly, limit, offset }) {
    const params = new URLSearchParams();
    if (activityType) params.append('activity_type', activityType);
    if (userId) params.append('user_id', userId);
    if (itemId) params.append('item_id', itemId);
    if (followingOnly) params.append('following_only', 'true');
    params.append('limit', limit || 50);
    params.append('offset', offset || 0);

    const response = await api.get(`/api/activities?${params}`);
    return response.data;
  },

  // 활동 생성/수정
  async createActivity(activityData) {
    const response = await api.post('/api/activities', activityData);
    return response.data;
  },

  async updateActivity(activityId, activityData) {
    const response = await api.put(`/api/activities/${activityId}`, activityData);
    return response.data;
  },

  async deleteActivity(activityId) {
    await api.delete(`/api/activities/${activityId}`);
  },

  // 좋아요
  async toggleLike(activityId) {
    const response = await api.post(`/api/activities/${activityId}/like`);
    return response.data;
  },

  // 댓글
  async getComments(activityId) {
    const response = await api.get(`/api/activities/${activityId}/comments`);
    return response.data;
  },

  async createComment(activityId, content, parentCommentId = null) {
    const response = await api.post(`/api/activities/${activityId}/comments`, {
      content,
      parent_comment_id: parentCommentId
    });
    return response.data;
  }
};
```

### 4.2 React Hooks 통합

```javascript
// useActivity.js
export function useActivities(filters) {
  return useQuery(
    ['activities', filters],
    () => activityService.getActivities(filters),
    { staleTime: 30000 }
  );
}

export function useActivityActions(activityId) {
  const queryClient = useQueryClient();

  const likeMutation = useMutation(
    () => activityService.toggleLike(activityId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['activities']);
      }
    }
  );

  const commentMutation = useMutation(
    (data) => activityService.createComment(activityId, data.content, data.parentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['activities', activityId, 'comments']);
      }
    }
  );

  return {
    like: likeMutation.mutate,
    comment: commentMutation.mutate
  };
}
```

---

## 마이그레이션 단계

### Step 1: 준비 (1-2일)
- [ ] 리팩토링 계획 리뷰 및 확정
- [ ] 백업 생성
- [ ] 테스트 환경 구축

### Step 2: 데이터베이스 마이그레이션 (2-3일)
- [ ] `activities` 테이블 생성
- [ ] 기존 데이터 마이그레이션 스크립트 작성
  - `user_ratings` → `activities`
  - `character_ratings` → `activities`
  - `user_reviews` 내용 병합
  - `character_reviews` 내용 병합
- [ ] 트리거 업데이트 (원본 테이블 변경 시 activities 동기화)
- [ ] 좋아요/댓글 테이블 마이그레이션
- [ ] 인덱스 최적화

### Step 3: 백엔드 API 구현 (3-4일)
- [ ] `/api/activities` 엔드포인트 구현
- [ ] 기존 API를 새 API로 프록시
- [ ] 테스트 작성 및 검증

### Step 4: 프론트엔드 컴포넌트 구현 (3-4일)
- [ ] `ActivityCard` 및 하위 컴포넌트 구현
- [ ] `activityService.js` 구현
- [ ] React Hooks 구현
- [ ] Storybook에서 컴포넌트 테스트

### Step 5: 페이지별 마이그레이션 (4-5일)
- [ ] Feed.jsx 마이그레이션
- [ ] AnimeDetail.jsx 마이그레이션
- [ ] CharacterDetail.jsx 마이그레이션
- [ ] MyAniPass.jsx 마이그레이션
- [ ] 각 페이지 테스트

### Step 6: 클린업 (1-2일)
- [ ] 구 API 엔드포인트 제거
- [ ] 구 서비스 파일 제거
- [ ] 구 테이블 제거 (데이터 검증 후)
- [ ] 사용하지 않는 코드 제거

### Step 7: 최적화 및 모니터링 (ongoing)
- [ ] 성능 측정
- [ ] 쿼리 최적화
- [ ] 캐싱 전략 적용
- [ ] 버그 수정

---

## 예상 효과

### 1. 개발 속도 향상
- 새 페이지 추가 시 `ActivityCard` 재사용
- 버그 수정 한 번에 모든 페이지 적용

### 2. 일관성 보장
- 모든 페이지에서 동일한 UI/UX
- 아바타, 좋아요, 댓글 모두 일관적으로 동작

### 3. 코드 감소
- 중복 코드 70% 감소 예상
- 테이블 수 50% 감소

### 4. 성능 향상
- 단일 테이블 조회 (조인 최소화)
- 인덱스 최적화로 빠른 조회

### 5. 유지보수성 향상
- 단일 소스 of truth
- 변경 사항 추적 용이

---

## 리스크 및 대응

### 리스크 1: 데이터 마이그레이션 실패
**대응**:
- 철저한 백업
- 단계별 롤백 계획
- 스테이징 환경에서 먼저 테스트

### 리스크 2: 성능 저하
**대응**:
- 쿼리 최적화
- 적절한 인덱싱
- 필요시 캐싱 레이어 추가

### 리스크 3: 기존 기능 손상
**대응**:
- 포괄적인 테스트 작성
- 페이지별 점진적 마이그레이션
- 카나리 배포

---

## 결론

이 리팩토링을 통해 AniPass는:
1. **단일 소스 of truth** - 모든 활동이 하나의 테이블에
2. **재사용 가능한 컴포넌트** - ActivityCard 하나로 모든 곳에서 사용
3. **일관된 사용자 경험** - 어디서 보든 동일한 UI/UX
4. **유지보수 용이** - 변경 사항 한 곳에만 적용

현재의 분산된 구조에서 **통합되고 표준화된 아키텍처**로 전환됩니다.
