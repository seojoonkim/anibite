#!/bin/bash
set -euo pipefail
export DATABASE_PATH="${DATABASE_PATH:-/app/data/anime.db}"
cd /app/backend
# No implicit touch, migration, chmod or backfill during a worker restart.
python -m migrations check
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
