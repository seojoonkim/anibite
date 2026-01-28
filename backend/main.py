"""
AniPass Backend - FastAPI Application
왓챠피디아 스타일 애니메이션 평가 플랫폼
Updated: 2026-01-18 - Added native title support for feed
"""
# Fix Windows console encoding issues
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import HTTPException
from config import ALLOWED_ORIGINS, COVER_IMAGES_DIR
import os

# Import API routers
from api import auth, anime, ratings, reviews, comments, users, series, characters, character_ratings, feed, follows, activity_comments, comment_likes, user_posts, character_reviews, notifications, activities, rating_pages, admin, admin_fix, admin_editor, debug_promotion, bookmarks

# Try to import image_proxy router (may fail if dependencies missing)
try:
    from routers import image_proxy
    IMAGE_PROXY_AVAILABLE = True
    print("[Startup] ✅ Image proxy router loaded successfully")
except Exception as e:
    IMAGE_PROXY_AVAILABLE = False
    print(f"[Startup] ❌ Failed to load image proxy router: {e}")
    import traceback
    traceback.print_exc()

app = FastAPI(
    title="AniPass API",
    description="애니메이션 평가 및 추천 플랫폼 API",
    version="1.0.0",
    redirect_slashes=False,  # Prevent HTTPS->HTTP redirect on Railway
)

# Startup event to ensure database schema is up to date
@app.on_event("startup")
async def startup_event():
    """Run on application startup - Complete initialization and backfill"""
    print("\n" + "="*60)
    print(">>> ANIPASS BACKEND STARTUP")
    print("="*60 + "\n")

    # 1. Schema updates
    print("[Startup] Ensuring database schema is up to date...")
    try:
        from scripts.ensure_schema import main as ensure_schema
        ensure_schema()
        print("[Startup] OK - Schema check complete")
    except Exception as e:
        print(f"[Startup] WARNING -Schema check failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Sync Korean character names (DISABLED - overwrites manual edits)
    # This script overwrites manually edited names from admin panel
    # Only run this manually if you need to bulk update from korean_names.json
    # print("[Startup] Syncing Korean character names...")
    # try:
    #     from scripts.sync_korean_names import sync_korean_names
    #     sync_korean_names()
    #     print("[Startup] OK - Korean names sync complete")
    # except Exception as e:
    #     print(f"[Startup] WARNING -Korean names sync failed: {e}")
    #     import traceback
    #     traceback.print_exc()

    # 2.5. Ensure UNIQUE constraints to prevent duplicate ratings
    print("[Startup] Ensuring UNIQUE constraints...")
    try:
        from scripts.ensure_unique_constraints import ensure_unique_constraints
        ensure_unique_constraints()
        print("[Startup] OK - UNIQUE constraints ensured")
    except Exception as e:
        print(f"[Startup] WARNING - UNIQUE constraints check failed: {e}")
        import traceback
        traceback.print_exc()

    # 3. Create bookmarks table
    print("[Startup] Creating bookmarks table...")
    try:
        from database import get_db
        db = get_db()
        db.execute_update("""
            CREATE TABLE IF NOT EXISTS activity_bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, activity_id)
            )
        """)
        db.execute_update("CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON activity_bookmarks(user_id)")
        db.execute_update("CREATE INDEX IF NOT EXISTS idx_bookmarks_activity_id ON activity_bookmarks(activity_id)")
        print("[Startup] OK - Bookmarks table ready")
    except Exception as e:
        print(f"[Startup] WARNING -Failed to create bookmarks table: {e}")

    # 4. Add preferred_language column if needed
    print("\n[DB] Checking database schema...")
    try:
        from scripts.add_preferred_language import add_preferred_language_column
        add_preferred_language_column()
        print("✅ Database schema up to date!\n")
    except Exception as e:
        print(f"WARNING: Failed to update schema: {e}\n")

    # 5. Verify existing users (one-time migration for email verification feature)
    print("👤 Verifying existing users...")
    try:
        from scripts.verify_existing_users import verify_existing_users
        verify_existing_users()
        print("✅ Existing users verified!\n")
    except Exception as e:
        print(f"WARNING: Failed to verify existing users: {e}\n")

    # 6. Fix triggers
    print("🔧 Checking and fixing database triggers...")
    try:
        from scripts.fix_railway_triggers import fix_triggers
        fix_triggers()
        print("✅ Triggers fixed successfully!\n")
    except Exception as e:
        print(f"WARNING: Failed to fix triggers: {e}")
        print("Server will continue, but rating save may fail.\n")

    # 7. Add activity indexes for performance
    print("📊 Adding database indexes for performance...")
    try:
        from scripts.add_activity_indexes import add_indexes
        add_indexes()
        print("✅ Indexes created successfully!\n")
    except Exception as e:
        print(f"WARNING: Failed to add indexes: {e}")
        print("Server will continue, but queries may be slow.\n")

    # 8. CRITICAL: Backfill anime_title_native and item_title_native for ALL activities
    print("🌐 Backfilling Japanese titles for ALL activities...")
    try:
        from database import get_db
        db = get_db()

        # Check if columns exist
        columns = db.execute_query("PRAGMA table_info(activities)")
        column_names = [col[1] for col in columns]

        if 'anime_title_native' not in column_names:
            print("  Adding anime_title_native column...")
            db.execute_update("ALTER TABLE activities ADD COLUMN anime_title_native TEXT")

        if 'item_title_native' not in column_names:
            print("  Adding item_title_native column...")
            db.execute_update("ALTER TABLE activities ADD COLUMN item_title_native TEXT")

        # Backfill 1: Anime native titles for character activities
        db.execute_update("""
            UPDATE activities
            SET anime_title_native = (
                SELECT a.title_native
                FROM anime a
                WHERE a.id = activities.anime_id
            )
            WHERE activity_type IN ('character_rating', 'character_review')
            AND anime_id IS NOT NULL
            AND anime_title_native IS NULL
        """)

        # Backfill 2: Character native names
        db.execute_update("""
            UPDATE activities
            SET item_title_native = (
                SELECT c.name_native
                FROM character c
                WHERE c.id = activities.item_id
            )
            WHERE activity_type IN ('character_rating', 'character_review')
            AND item_id IS NOT NULL
            AND item_title_native IS NULL
        """)

        # Backfill 3: Anime native titles for anime activities (THIS WAS MISSING!)
        db.execute_update("""
            UPDATE activities
            SET item_title_native = (
                SELECT a.title_native
                FROM anime a
                WHERE a.id = activities.item_id
            )
            WHERE activity_type IN ('anime_rating', 'anime_review')
            AND item_id IS NOT NULL
            AND item_title_native IS NULL
        """)

        # Count results
        anime_char_count = db.execute_query("""
            SELECT COUNT(*) as count
            FROM activities
            WHERE activity_type IN ('character_rating', 'character_review')
            AND anime_title_native IS NOT NULL
        """, fetch_one=True)

        char_count = db.execute_query("""
            SELECT COUNT(*) as count
            FROM activities
            WHERE activity_type IN ('character_rating', 'character_review')
            AND item_title_native IS NOT NULL
        """, fetch_one=True)

        anime_count = db.execute_query("""
            SELECT COUNT(*) as count
            FROM activities
            WHERE activity_type IN ('anime_rating', 'anime_review')
            AND item_title_native IS NOT NULL
        """, fetch_one=True)

        print(f"✅ Backfilled:")
        print(f"   - {anime_char_count['count'] if anime_char_count else 0} character activity anime titles")
        print(f"   - {char_count['count'] if char_count else 0} character names")
        print(f"   - {anime_count['count'] if anime_count else 0} anime activity titles\n")
    except Exception as e:
        print(f"WARNING: Failed to backfill titles: {e}")
        print("Server will continue, but Japanese titles may not display.\n")
        import traceback
        traceback.print_exc()

    # 9. Debug: Log database info
    try:
        from config import DATABASE_PATH
        from database import get_db
        import os

        print(f"[Startup DEBUG] DATABASE_PATH: {DATABASE_PATH}")
        print(f"[Startup DEBUG] Database file exists: {os.path.exists(DATABASE_PATH)}")
        if os.path.exists(DATABASE_PATH):
            print(f"[Startup DEBUG] Database file size: {os.path.getsize(DATABASE_PATH)} bytes")

        db = get_db()
        user_posts = db.execute_query("SELECT COUNT(*) FROM user_posts")
        activities_posts = db.execute_query("SELECT COUNT(*) FROM activities WHERE activity_type = 'user_post'")
        print(f"[Startup DEBUG] user_posts count: {user_posts[0][0] if user_posts else 0}")
        print(f"[Startup DEBUG] activities (user_post) count: {activities_posts[0][0] if activities_posts else 0}")

        # Show recent user_posts
        recent_posts = db.execute_query("SELECT id, user_id, created_at FROM user_posts ORDER BY created_at DESC LIMIT 3")
        print(f"[Startup DEBUG] Recent user_posts:")
        for post in recent_posts:
            print(f"  - ID: {post[0]}, user_id: {post[1]}, created_at: {post[2]}")

        # Show user 4's activity breakdown
        user4_anime = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = 4 AND activity_type = 'anime_rating'")
        user4_char = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = 4 AND activity_type = 'character_rating'")
        user4_post = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = 4 AND activity_type = 'user_post'")
        user4_total = db.execute_query("SELECT COUNT(*) FROM activities WHERE user_id = 4")
        print(f"[Startup DEBUG] User 4 activities:")
        print(f"  - anime_rating: {user4_anime[0][0] if user4_anime else 0}")
        print(f"  - character_rating: {user4_char[0][0] if user4_char else 0}")
        print(f"  - user_post: {user4_post[0][0] if user4_post else 0}")
        print(f"  - TOTAL: {user4_total[0][0] if user4_total else 0}")
    except Exception as e:
        print(f"[Startup DEBUG] Failed to log database info: {e}")

    print("\n" + "="*60)
    print("✅ STARTUP COMPLETE")
    print("="*60 + "\n")

# Debug: Print allowed origins on startup
print(f"[CORS] Allowed origins: {ALLOWED_ORIGINS}")

# CORS middleware - Must be added before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Exception handler to ensure CORS headers on error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Add CORS headers to HTTP exception responses"""
    origin = request.headers.get("origin")

    # Check if origin is allowed
    if origin and origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        headers = {}

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


# Handle all other exceptions (500 errors)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with CORS headers"""
    origin = request.headers.get("origin")

    # Log the error
    print(f"[ERROR] {type(exc).__name__}: {str(exc)}")
    import traceback
    traceback.print_exc()

    # Add CORS headers if origin is allowed
    if origin and origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        headers = {}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers=headers,
    )


# Static files (images)
# 전체 images 폴더를 마운트 (covers, covers_large 등 포함)
images_root = COVER_IMAGES_DIR.parent  # data/images/
if os.path.exists(images_root):
    app.mount("/images", StaticFiles(directory=str(images_root)), name="images")

# Static files (user uploads - avatars)
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Note: Startup event is now consolidated above (lines 25-240)
# This duplicate was removed to prevent conflicts


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to AniPass API",
        "docs": "/docs",
        "version": "1.0.1"
    }


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": "2026-01-13"}


# Legacy image proxy removed - now using routers/image_proxy.py with auto-download functionality


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])  # Unified activities API
app.include_router(rating_pages.router, prefix="/api/rating-pages", tags=["Rating Pages"])  # Ultra-fast rating pages
app.include_router(anime.router, prefix="/api/anime", tags=["Anime"])
app.include_router(ratings.router, prefix="/api/ratings", tags=["Ratings"])
app.include_router(character_ratings.router, prefix="/api/character-ratings", tags=["Character Ratings"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(character_reviews.router, prefix="/api/character-reviews", tags=["Character Reviews"])
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(series.router, prefix="/api/series", tags=["Series"])
app.include_router(characters.router, prefix="/api/characters", tags=["Characters"])
app.include_router(feed.router, prefix="/api/feed", tags=["Feed"])
app.include_router(follows.router, prefix="/api/follows", tags=["Follows"])
app.include_router(activity_comments.router, prefix="/api/activity-comments", tags=["Activity Comments"])
app.include_router(comment_likes.router, prefix="/api/comment-likes", tags=["Comment Likes"])
app.include_router(user_posts.router, prefix="/api/user-posts", tags=["User Posts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["Bookmarks"])
if IMAGE_PROXY_AVAILABLE:
    app.include_router(image_proxy.router, prefix="/api", tags=["Image Proxy"])  # Auto-download images from AniList
    print("[Startup] ✅ Image proxy router registered")
else:
    print("[Startup] ⚠️ Image proxy router NOT registered (import failed)")
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_fix.router, prefix="/api/admin-fix", tags=["Admin Fix"])
app.include_router(admin_editor.router, prefix="/api/admin/editor", tags=["Admin Editor"])
app.include_router(debug_promotion.router, prefix="/api/debug", tags=["Debug"])


# Serve React frontend static files
# This should be mounted AFTER all API routes to avoid conflicts
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    # Mount static assets (JS, CSS, images, etc.)
    # Use StaticFiles with html=True to properly serve all frontend files
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="frontend-assets")

    # Mount placeholders directory if it exists
    placeholders_dir = os.path.join(frontend_dist, "placeholders")
    if os.path.exists(placeholders_dir):
        app.mount("/placeholders", StaticFiles(directory=placeholders_dir), name="placeholders")

    # Catch-all route for React Router - serve index.html for all non-API routes
    # This is registered AFTER all API routes, so API routes take precedence
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response

    @app.middleware("http")
    async def serve_frontend_middleware(request, call_next):
        """Serve React frontend for non-API, non-static routes"""
        response = await call_next(request)

        # If the response is 404 and not an API route, serve index.html
        path = request.url.path
        if response.status_code == 404 and not path.startswith("/api/") and not path.startswith("/images/"):
            # Check if it's a static file request
            file_path = os.path.join(frontend_dist, path.lstrip("/"))
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            # Serve index.html for React Router
            index_path = os.path.join(frontend_dist, "index.html")
            if os.path.isfile(index_path):
                return FileResponse(index_path)

        return response

    print(f"[Startup] OK - Serving React frontend from: {frontend_dist}")
else:
    print(f"[Startup] WARNING - Frontend dist not found at: {frontend_dist}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
