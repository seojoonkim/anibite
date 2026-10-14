# 데이터베이스 백업 가이드

## 🔄 자동 백업 (클라우드)

### GitHub Actions 자동 백업

**백업 스케줄:**
- ✅ **매일 새벽 3시** (한국시간) - GitHub Artifacts에 90일간 보관
- ✅ **매주 일요일** - GitHub Releases에 영구 보관

**설정 방법:**

1. **Railway Token 발급**
   ```bash
   railway login
   railway whoami --token
   ```

2. **GitHub Secrets 등록**
   - GitHub 레포지토리 → Settings → Secrets and variables → Actions
   - `RAILWAY_TOKEN` 추가 (위에서 발급받은 토큰)

3. **백업 확인**
   - GitHub → Actions → "Backup Railway Database"
   - 최근 실행 결과 확인

4. **수동 백업 실행**
   - GitHub → Actions → "Backup Railway Database" → Run workflow

---

## 📥 백업 다운로드

### 1. GitHub Artifacts (최근 7일)

1. GitHub → Actions → "Backup Railway Database" 워크플로우
2. 원하는 날짜의 실행 선택
3. "Artifacts" 섹션에서 다운로드

### 2. GitHub Releases (장기 보관)

1. GitHub → Releases
2. `backup-YYYYMMDD_HHMMSS` 태그 찾기
3. `anime_*.db.gz` 파일 다운로드

---

## 📤 백업 복원

### Railway로 복원

```bash
# 1. 압축 해제 (Releases에서 다운로드한 경우)
gunzip anime_20260128_030000.db.gz

# 2. Railway에 업로드
./scripts/restore_db.sh anime_20260128_030000.db

# 3. Railway 재배포
# Railway Dashboard → Deployments → Redeploy
```

### 로컬에서 테스트

```bash
# 압축 해제
gunzip anime_20260128_030000.db.gz

# 로컬 data/ 폴더에 복사
cp anime_20260128_030000.db data/anime.db

# 백엔드 실행
cd backend
python3 main.py
```

---

## 🖥️ 수동 백업 (로컬)

### Railway → 로컬

```bash
# 백업 실행
./scripts/backup_db.sh

# 백업 파일 위치
# backups/railway/anime_YYYYMMDD_HHMMSS.db
```

### 로컬 → Railway

```bash
# 복원 실행
./scripts/restore_db.sh backups/railway/anime_20260128_030000.db
```

---

## 📊 백업 상태 확인

### GitHub Actions 상태

```bash
# GitHub CLI 설치 필요
gh run list --workflow="backup-db.yml" --limit 5
```

### 로컬 백업 목록

```bash
ls -lh backups/railway/
```

---

## ⚠️ 주의사항

1. **복원 전 확인**
   - 복원하면 현재 Railway DB가 **완전히 덮어써집니다**
   - 복원 전 현재 DB 백업 권장: `./scripts/backup_db.sh`

2. **용량 관리**
   - GitHub Artifacts: 자동으로 최근 7개만 유지
   - GitHub Releases: 수동 삭제 필요 (저장공간 무제한)
   - 로컬 백업: 자동으로 최근 10개만 유지

3. **보안**
   - `RAILWAY_TOKEN`은 절대 공개하지 마세요
   - GitHub Private Repository 사용 권장
   - 백업 파일에는 유저 비밀번호 해시가 포함되어 있습니다

---

## 🆘 문제 해결

### GitHub Actions 백업 실패

```bash
# Railway CLI 수동 테스트
railway login
railway run --service anipass bash -c "cat /app/data/anime.db" > test.db

# 파일 크기 확인
du -h test.db
```

### Railway Token 만료

```bash
# 새 토큰 발급
railway logout
railway login
railway whoami --token

# GitHub Secrets 업데이트
```

### 복원 실패

```bash
# Railway Volume 확인
railway run --service anipass ls -la /app/data/

# 권한 확인
railway run --service anipass bash -c "touch /app/data/test.txt && rm /app/data/test.txt"
```

---

## 📞 백업 일정 변경

`.github/workflows/backup-db.yml` 파일에서 `cron` 수정:

```yaml
on:
  schedule:
    # 매일 새벽 3시 (한국시간)
    - cron: '0 18 * * *'  # UTC 18:00 = KST 03:00

    # 매일 자정 (한국시간)
    # - cron: '0 15 * * *'  # UTC 15:00 = KST 00:00

    # 매주 월요일 새벽 3시
    # - cron: '0 18 * * 1'

    # 매월 1일 새벽 3시
    # - cron: '0 18 1 * *'
```

---

## ✅ 백업 체크리스트

- [ ] GitHub Actions에 `RAILWAY_TOKEN` 설정됨
- [ ] 자동 백업이 매일 실행되는지 확인
- [ ] 최근 백업 파일 다운로드 테스트
- [ ] 복원 스크립트 테스트 (로컬에서)
- [ ] 복원 시나리오 문서화

---

**마지막 업데이트:** 2026-01-28
