# 🎌 AniList 크롤러 - 애니 평가 플랫폼 DB

인기 애니메이션 3,000개의 완전한 데이터를 수집하는 크롤러입니다.

## 📊 수집 데이터 규모

| 항목 | 개수 | 용량 |
|------|------|------|
| 애니메이션 | 3,000개 | - |
| 캐릭터 | ~25,000명 | - |
| 성우 | ~5,000명 | - |
| 스태프 | ~10,000명 | - |
| **데이터 총합** | - | **~226 MB** |
| 커버 이미지 | 3,000장 | **~161 MB** |
| **전체 총합** | - | **~387 MB** |

## 📁 프로젝트 구조

```
anime-db/
├── schema.sql          # DB 스키마 정의
├── crawler.py          # 메인 크롤러
├── anilist_client.py   # AniList API 클라이언트
├── db_utils.py         # DB 조회 유틸리티
├── test_sample.py      # 샘플 데이터 테스트
├── anime.db            # SQLite 데이터베이스 (크롤링 후 생성)
└── images/
    └── covers/         # 커버 이미지 저장 폴더
```

## 🚀 사용법

### 1. 크롤링 실행

```bash
cd anime-db
python3 crawler.py
```

크롤링은 4단계로 진행됩니다:
1. **애니메이션 기본 정보** (~4분, Page 쿼리)
2. **캐릭터/성우** (~5시간)
3. **스태프** (~2시간)
4. **커버 이미지 다운로드** (~1시간)

총 예상 시간: **~8시간** (Rate Limit: 90 req/분)

### 2. 데이터 조회

```python
from db_utils import AnimeDB

db = AnimeDB('anime.db')

# 인기 애니메이션
popular = db.get_popular_anime(limit=10)

# 애니 상세 정보
anime = db.get_anime(16498)  # 진격의 거인

# 애니메이션 검색
results = db.search_anime("진격")

# 장르별 검색
action_anime = db.get_anime_by_genre("Action")

# 시즌별 검색
spring_2024 = db.get_anime_by_season(2024, "SPRING")

# 캐릭터 정보
characters = db.get_anime_characters(16498)

# 성우 정보
voice_actors = db.get_anime_voice_actors(16498)

db.close()
```

## 📋 DB 스키마

### 주요 테이블

| 테이블 | 설명 |
|--------|------|
| `anime` | 애니메이션 기본 정보 (제목, 점수, 에피소드 등) |
| `character` | 캐릭터 정보 (이름, 설명, 이미지 URL) |
| `staff` | 스태프/성우 정보 |
| `genre` | 장르 목록 |
| `tag` | 상세 태그 (Shounen, Isekai 등) |
| `studio` | 제작 스튜디오 |

### 연결 테이블

| 테이블 | 설명 |
|--------|------|
| `anime_genre` | 애니-장르 연결 |
| `anime_tag` | 애니-태그 연결 (관련도 포함) |
| `anime_studio` | 애니-스튜디오 연결 |
| `anime_character` | 애니-캐릭터 연결 (역할 포함) |
| `anime_staff` | 애니-스태프 연결 (직책 포함) |
| `character_voice_actor` | 캐릭터-성우 연결 |
| `anime_relation` | 관련 작품 (시퀄, 프리퀄 등) |
| `anime_recommendation` | 추천 작품 |

## 🖼️ 이미지 전략

### Phase 1 (현재)
- ✅ 애니 커버 이미지: 로컬 저장 (~161 MB)
- 🌐 배너/캐릭터/성우 이미지: CDN URL만 저장

### Phase 2 (나중에 추가 가능)
```bash
# 캐릭터 이미지 추가: +684 MB
# 성우/스태프 이미지: +410 MB  
# 배너 이미지: +410 MB
# → 완전체: 1.9 GB
```

## ⚙️ 설정 변경

`crawler.py` 상단에서 조정 가능:

```python
TARGET_ANIME_COUNT = 3000   # 크롤링할 애니 수
CHARS_PER_ANIME = 25        # 애니당 캐릭터 수
STAFF_PER_ANIME = 25        # 애니당 스태프 수
```

## 🎯 활용 예시

### 스와이프 카드용 데이터
```python
anime = db.get_popular_anime(limit=1)[0]
card = {
    "id": anime['id'],
    "title": anime['title_english'] or anime['title_romaji'],
    "image": anime['cover_image_local'],  # 로컬 이미지
    "score": anime['average_score'],
    "episodes": anime['episodes'],
}
```

### 상세 페이지용 데이터
```python
anime = db.get_anime(anime_id)
characters = db.get_anime_characters(anime_id)
voice_actors = db.get_anime_voice_actors(anime_id)
```

## 📝 AniList API 정보

- **엔드포인트**: `https://graphql.anilist.co`
- **Rate Limit**: 90 requests/minute
- **인증**: 불필요 (공개 데이터)
- **문서**: https://anilist.gitbook.io/anilist-apiv2-docs
