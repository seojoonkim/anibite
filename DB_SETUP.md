# 데이터베이스 설정 가이드

## ⚠️ 중요 변경사항 (2026-01-28)

**데이터베이스 파일이 Git에서 제거되었습니다.**

이제 프로덕션 DB는 **Railway Volume**에 저장되어 배포 시에도 안전하게 유지됩니다.

---

## 🔧 Railway Volume 설정 (필수)

### 1. Railway Dashboard 설정

1. https://railway.app 접속
2. `anibite` 프로젝트 선택
3. Backend 서비스 클릭
4. **Settings** → **Volumes** → **+ Add Volume**
5. Mount Path: `/app/data`
6. **Add** 클릭

### 2. 재배포

**Deployments** 탭 → 최신 배포 → **⋮** → **Redeploy**

---

## 💾 DB 백업 및 복원

### 로컬 DB 백업

```bash
cp data/anime.db data/anime.db.backup.$(date +%Y%m%d)
```

### Railway에 DB 업로드

#### 방법 1: Railway CLI (권장)

```bash
# 1. CLI 설치
npm install -g @railway/cli

# 2. 로그인 및 연결
railway login
railway link

# 3. DB 업로드
railway run bash -c "cat > /app/data/anime.db" < data/anime.db
```

#### 방법 2: 스크립트 사용

```bash
python3 scripts/upload_db_to_railway.py
```

### Railway에서 DB 다운로드

```bash
railway run bash -c "cat /app/data/anime.db" > data/anime.db.downloaded
```

---

## 🚨 문제 해결

### 이름 변경이 리셋되는 문제

**원인**: DB가 Git에 있어서 배포 시 덮어써짐
**해결**: Railway Volume 설정 (위 참조)

### DB 파일이 없다는 에러

**원인**: Volume이 설정되지 않았거나 DB 파일이 업로드되지 않음
**해결**:
1. Railway Volume 확인
2. DB 파일 업로드 (위 참조)

### 권한 에러

**원인**: Railway에서 `/app/data` 디렉토리 권한 문제
**해결**: Dockerfile에서 권한 설정
```dockerfile
RUN mkdir -p /app/data && chmod 777 /app/data
```

---

## 📂 DB 파일 위치

- **로컬 개발**: `data/anime.db`
- **Railway 프로덕션**: `/app/data/anime.db` (Volume)

---

## ✅ 설정 완료 확인

1. Railway에서 재배포 완료
2. 어드민에서 캐릭터 이름 변경
3. 몇 시간 후 확인 → **이름 유지됨!** ✨

---

## 🆘 도움말

문제가 발생하면:
1. Railway Logs 확인
2. Volume 마운트 확인: `/app/data`
3. DB 파일 존재 확인: `railway run ls -la /app/data`

더 자세한 가이드: `/tmp/RAILWAY_VOLUME_SETUP.md`
