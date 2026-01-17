# CLAUDE.md - AniPass 작업 컨텍스트

## 현재 작업 (2025-01-17)

### 캐릭터 한국어 이름 업데이트 작업

**목표**: 모든 캐릭터의 한국어 이름을 구글 검색으로 공식 이름으로 업데이트

**상태**: 진행 중

**스크립트**: `data/update_all_korean_names.py`

**진행 상황 파일**: `data/update_all_korean_progress.json`

### 실행 방법
```bash
python3 data/update_all_korean_names.py
```

### 중단 후 재개
- 스크립트가 중단되어도 `update_all_korean_progress.json`에 진행 상황이 저장됨
- 다시 실행하면 자동으로 이어서 처리

### 스크립트 버전들
| 파일 | 설명 | 상태 |
|------|------|------|
| `crawl_namuwiki_character_v8.py` | Playwright 기반 나무위키 크롤러 | 사용 가능 |
| `crawl_namuwiki_character_v9.py` | httpx 기반 (나무위키 차단됨) | 차단됨 |
| `crawl_namuwiki_character_v10.py` | 애니 제목과 함께 검색 | 차단됨 |
| `update_all_korean_names.py` | 구글 검색 기반 (현재 메인) | **사용 중** |

### 주요 설정
- `MAX_WORKERS`: 5 (동시 브라우저 수)
- `MIN_DELAY`: 2초, `MAX_DELAY`: 4초 (구글 rate limit 대응)
- 예상 속도: 분당 ~100개

---

## 데이터베이스 정보

- 경로: `data/anime.db`
- 캐릭터 테이블: `character`
- 한국어 이름 컬럼: `name_korean`

### 통계 (마지막 확인)
- 전체 캐릭터: 47,557개
- 한국어 이름 있음: 47,365개
- 한국어 이름 없음: 192개

---

## 다음 작업

1. `update_all_korean_names.py` 실행 완료
2. 결과 검증 (샘플 체크)
3. 프론트엔드에서 한국어 이름 표시 확인

---

## 문제 해결

### 나무위키 429 에러
나무위키가 httpx 요청을 차단함. Playwright(브라우저)만 사용 가능.

### 구글 봇 감지
- 랜덤 딜레이 사용 (2~4초)
- 다양한 User-Agent 사용
- headless 브라우저 설정 최적화
