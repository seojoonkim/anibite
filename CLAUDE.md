# CLAUDE.md - AniPass 작업 컨텍스트

## 현재 작업 (2025-01-17)

### 캐릭터 한국어 이름 전체 재검증 작업

**목표**: 기존 한국어 이름에 오류가 많아 모든 캐릭터의 한국어 이름을 구글 검색으로 재검증/업데이트

**방법**: `"영어이름" 이름` 형식으로 구글 검색 → 공식 한국어 이름 추출

**상태**: 진행 중

**스크립트**: `data/update_all_korean_names.py`

**진행 상황 파일**: `data/update_all_korean_progress.json`

---

## 실행 방법

### 처음부터 시작 (기존 진행 초기화)
```bash
rm -f data/update_all_korean_progress.json && python3 data/update_all_korean_names.py
```

### 중단된 곳에서 이어서
```bash
python3 data/update_all_korean_names.py
```

### 옵션
```bash
python3 data/update_all_korean_names.py --workers 5 --min-delay 2 --max-delay 4 --limit 100
```

---

## 스크립트 특징 (v2 - 2025-01-17 업데이트)

### 안정성 강화
- 개별 캐릭터 처리 실패 시 에러 로그 후 계속 진행
- 브라우저 크래시 시 자동 재시작 (최대 10회)
- Ctrl+C / 종료 시 즉시 진행 상황 저장
- `atexit` 핸들러로 비정상 종료에도 저장

### 저장 주기
- **10개마다** 진행 상황 저장 및 출력
- 60초마다 보조 저장

### 구글 봇 감지 우회
- 랜덤 딜레이 2~4초
- 5개 다양한 User-Agent 로테이션
- `webdriver` 속성 숨김
- 연속 실패 시 브라우저 재시작

---

## 주요 설정 (`update_all_korean_names.py`)

| 설정 | 값 | 설명 |
|------|-----|------|
| `MAX_WORKERS` | 5 | 동시 브라우저 수 |
| `MIN_DELAY` | 2.0초 | 최소 딜레이 |
| `MAX_DELAY` | 4.0초 | 최대 딜레이 |
| `SAVE_EVERY` | 10 | N개마다 저장 |
| `MIN_SCORE` | 3 | 후보 점수 최소 기준 |

---

## 데이터베이스 정보

- 경로: `data/anime.db`
- 캐릭터 테이블: `character`
- 한국어 이름 컬럼: `name_korean`

### 통계
- 전체 캐릭터: 47,557개

### 문제 있던 예시
| 영어 이름 | 기존 한국어 | 올바른 한국어 |
|----------|-------------|---------------|
| Luffy Monkey | 원피스 | 몽키 D. 루피 |
| Eren Yeager | 에렌・이에가 | 에렌 예거 |
| Zoro Roronoa | 로로노아・조로 | 로로노아 조로 |

---

## 스크립트 버전들

| 파일 | 설명 | 상태 |
|------|------|------|
| `update_all_korean_names.py` | 구글 검색 기반 (안정성 강화) | **사용 중** |
| `crawl_namuwiki_character_v8.py` | Playwright 기반 나무위키 크롤러 | 사용 가능 |
| `crawl_namuwiki_character_v9.py` | httpx 기반 (나무위키 차단됨) | 차단됨 |
| `crawl_namuwiki_character_v10.py` | 애니 제목과 함께 검색 | 차단됨 |

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

### 스크립트 다운 시
- 진행 상황이 `update_all_korean_progress.json`에 자동 저장됨
- 다시 실행하면 자동으로 이어서 처리
- Ctrl+C로 안전하게 중단 가능
