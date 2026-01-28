#!/bin/bash
set -e

echo "========================================"
echo "AniPass Docker Startup"
echo "========================================"

# Check if volume DB exists
if [ ! -f "/app/data/anime.db" ]; then
    echo "⚠️  Volume DB not found at /app/data/anime.db"
    echo "⚠️  Please upload your database to Railway Volume"
    echo "⚠️  See DB_SETUP.md for instructions"
    echo ""
    echo "Creating empty database for now..."

    # Create empty database (will be initialized by backend)
    touch /app/data/anime.db
    chmod 666 /app/data/anime.db
    echo "✅ Empty DB file created"
else
    echo "✅ Volume DB found at /app/data/anime.db"
    echo "📊 DB size: $(du -h /app/data/anime.db | cut -f1)"
fi

# Set DATABASE_PATH environment variable
export DATABASE_PATH="/app/data/anime.db"

echo "========================================"
echo "Starting uvicorn server..."
echo "========================================"

# Start uvicorn
cd /app/backend
exec uvicorn main:app --host 0.0.0.0 --port 8000
