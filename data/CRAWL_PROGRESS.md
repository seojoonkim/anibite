# 캐릭터 한국어 이름 크롤링 작업 기록

## 작업 개요
- 목적: 나무위키에서 캐릭터 한국어 이름을 크롤링하여 DB에 추가
- 스크립트: `data/crawl_namuwiki_verified.py`

## 작업 진행 상황

### 2026-01-16 작업
1. **50개 테스트 완료** - 성공
2. **1000개로 확장** - `MAX_CHARACTERS = 1000`으로 변경 완료

### 실행 방법
```bash
cd /Users/gimseojun/Documents/Git_Projects/anipass/data
python crawl_namuwiki_verified.py
```

### 주요 설정값
- `MAX_CHARACTERS = 1000` - 처리할 캐릭터 수
- `MAX_LINKS_PER_ANIME = 50` - 애니메이션당 최대 캐릭터 링크 수
- `REQUEST_DELAY = 1.0` - 요청 간 딜레이 (초)
- `SAVE_INTERVAL = 50` - 진행상황 저장 간격

### 관련 파일
- `backend/scripts/add_character_korean_names.py` - DB 컬럼 추가 스크립트
- `data/crawl_namuwiki_verified.py` - 메인 크롤링 스크립트 (검증 포함)
- `data/crawl_namuwiki_playwright.py` - 초기 버전 스크립트

## 다음 할 일
- [ ] 1000개 크롤링 실행
- [ ] 결과 확인 후 더 많은 캐릭터로 확장 검토
