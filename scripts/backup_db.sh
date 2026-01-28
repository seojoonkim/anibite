#!/bin/bash
#
# Railway DB Backup Script
# Railway Volume의 데이터베이스를 로컬로 백업합니다
#
# 사용법:
#   ./scripts/backup_db.sh
#

set -e

echo "======================================"
echo "Railway DB Backup"
echo "======================================"

# Backup directory
BACKUP_DIR="backups/railway"
mkdir -p "$BACKUP_DIR"

# Generate filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/anime_${TIMESTAMP}.db"

echo ""
echo "📥 Downloading database from Railway..."
echo "   Target: $BACKUP_FILE"
echo ""

# Download DB from Railway
railway run --service anipass bash -c "cat /app/data/anime.db" > "$BACKUP_FILE"

# Check if download was successful
if [ -f "$BACKUP_FILE" ]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "✅ Backup successful!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $FILE_SIZE"

    # Keep only last 10 backups
    echo ""
    echo "🗑️  Cleaning old backups (keeping last 10)..."
    ls -t "$BACKUP_DIR"/anime_*.db | tail -n +11 | xargs -r rm -f

    REMAINING=$(ls -1 "$BACKUP_DIR"/anime_*.db | wc -l)
    echo "   Remaining backups: $REMAINING"

    echo ""
    echo "======================================"
    echo "✅ Backup Complete"
    echo "======================================"
else
    echo ""
    echo "❌ Backup failed!"
    exit 1
fi
