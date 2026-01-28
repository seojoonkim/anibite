#!/bin/bash
#
# Backup Setup Script
# Railway Token을 GitHub Secrets에 자동으로 등록합니다
#

set -e

echo "======================================"
echo "백업 시스템 설정"
echo "======================================"
echo ""

# Step 1: Railway Token 생성
echo "1️⃣  Railway API Token 생성"
echo ""
echo "브라우저에서 Railway Token 생성 페이지를 엽니다..."
sleep 1
open "https://railway.app/account/tokens"

echo ""
echo "다음 단계를 따라주세요:"
echo "  1. 페이지가 열리면 'Create new token' 클릭"
echo "  2. Token 이름: 'GitHub Actions Backup'"
echo "  3. 생성된 Token을 복사하세요"
echo ""
read -p "Token을 복사했으면 여기에 붙여넣으세요: " RAILWAY_TOKEN

if [ -z "$RAILWAY_TOKEN" ]; then
    echo ""
    echo "❌ Token이 비어있습니다. 취소합니다."
    exit 1
fi

echo ""
echo "✅ Railway Token 확인됨"

# Step 2: GitHub CLI 로그인
echo ""
echo "2️⃣  GitHub 로그인"
echo ""

# Check if already logged in
if ! gh auth status &>/dev/null; then
    echo "GitHub CLI에 로그인합니다..."
    echo "브라우저가 열리면 로그인해주세요."
    echo ""
    gh auth login
else
    echo "✅ 이미 GitHub에 로그인되어 있습니다"
fi

# Step 3: Set GitHub Secret
echo ""
echo "3️⃣  GitHub Secrets 등록"
echo ""

# Get current repo
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Repository: $REPO"

# Set secret
echo ""
echo "RAILWAY_TOKEN을 GitHub Secrets에 등록 중..."
echo "$RAILWAY_TOKEN" | gh secret set RAILWAY_TOKEN

echo ""
echo "✅ GitHub Secret 등록 완료!"

# Step 4: Test backup
echo ""
echo "4️⃣  백업 테스트 (선택사항)"
echo ""
read -p "지금 수동 백업을 실행하시겠습니까? (y/n): " RUN_BACKUP

if [ "$RUN_BACKUP" = "y" ] || [ "$RUN_BACKUP" = "Y" ]; then
    echo ""
    echo "백업 워크플로우 실행 중..."
    gh workflow run backup-db.yml

    echo ""
    echo "✅ 백업 시작됨!"
    echo ""
    echo "실행 상태 확인:"
    echo "  gh run list --workflow=backup-db.yml --limit 1"
    echo ""
    echo "또는 GitHub에서 확인:"
    echo "  https://github.com/$REPO/actions/workflows/backup-db.yml"
fi

echo ""
echo "======================================"
echo "✅ 설정 완료!"
echo "======================================"
echo ""
echo "📅 백업 스케줄:"
echo "   - 6시간마다 자동 백업 (09:00, 15:00, 21:00, 03:00 KST)"
echo "   - GitHub Artifacts: 최근 30개 보관"
echo "   - GitHub Releases: 매일 1개 영구 보관"
echo ""
echo "📖 상세 가이드: BACKUP_GUIDE.md"
echo ""
