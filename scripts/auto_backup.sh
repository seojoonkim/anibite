#!/bin/bash
#
# Auto Backup Script (for Cron)
# 자동으로 Railway DB를 백업합니다
#
# Cron 설정 예시 (매일 새벽 3시):
#   0 3 * * * cd /path/to/anibite && ./scripts/auto_backup.sh >> logs/backup.log 2>&1
#
# Cron 설정 예시 (매주 일요일 새벽 3시):
#   0 3 * * 0 cd /path/to/anibite && ./scripts/auto_backup.sh >> logs/backup.log 2>&1
#

set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting auto backup..."

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Run backup
./scripts/backup_db.sh

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto backup complete"
