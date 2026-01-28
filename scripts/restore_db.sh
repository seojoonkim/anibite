#!/bin/bash
#
# Railway DB Restore Script
# 로컬 백업 파일을 Railway Volume으로 복원합니다
#
# 사용법:
#   ./scripts/restore_db.sh [backup_file]
#
# 예시:
#   ./scripts/restore_db.sh backups/railway/anime_20260128_180000.db
#

set -e

echo "======================================"
echo "Railway DB Restore"
echo "======================================"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo ""
    echo "❌ Error: Please specify a backup file"
    echo ""
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh backups/railway/anime_*.db 2>/dev/null | tail -10 || echo "  (no backups found)"
    echo ""
    exit 1
fi

BACKUP_FILE="$1"

# Check if file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo ""
    echo "❌ Error: File not found: $BACKUP_FILE"
    exit 1
fi

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "📤 Restoring database to Railway..."
echo "   Source: $BACKUP_FILE"
echo "   Size: $FILE_SIZE"
echo ""

# Warning
echo "⚠️  WARNING: This will OVERWRITE the current Railway database!"
echo ""
read -p "Are you sure? (type 'yes' to continue): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "❌ Restore cancelled"
    exit 1
fi

echo ""
echo "📤 Uploading to Railway..."

# Upload to Railway
railway run --service anipass bash -c "cat > /app/data/anime.db" < "$BACKUP_FILE"

echo ""
echo "✅ Restore complete!"
echo ""
echo "⚠️  Please redeploy the Railway service to ensure the DB is properly loaded"
echo ""
echo "======================================"
echo "✅ Restore Complete"
echo "======================================"
