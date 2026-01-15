"""
AniPass Backend - FastAPI Application
왓챠피디아 스타일 애니메이션 평가 플랫폼
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from config import ALLOWED_ORIGINS, COVER_IMAGES_DIR
import os

# Import API routers
from api import auth, anime, ratings, reviews, comments, users, series, characters, character_ratings, feed, follows, activity_comments, activity_likes, comment_likes, user_posts, character_reviews, notifications, activities, rating_pages

app = FastAPI(
    title="AniPass API",
    description="애니메이션 평가 및 추천 플랫폼 API",
    version="1.0.0",
    redirect_slashes=False,  # Prevent HTTPS->HTTP redirect on Railway
)

# Startup event to ensure database schema is up to date
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("[Startup] Ensuring database schema is up to date...")
    try:
        from scripts.ensure_schema import main as ensure_schema
        ensure_schema()
        print("[Startup] ✓ Schema check complete")
    except Exception as e:
        print(f"[Startup] ⚠️  Schema check failed: {e}")
        # Don't fail startup, just log the error
        import traceback
        traceback.print_exc()

    # Debug: Log database info
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
    except Exception as e:
        print(f"[Startup DEBUG] Failed to log database info: {e}")

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


# Startup event - Fix triggers on server start
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 트리거 자동 수정"""
    print("\n🔧 Checking and fixing database triggers...")
    try:
        from scripts.fix_railway_triggers import fix_triggers
        fix_triggers()
        print("✅ Triggers fixed successfully!\n")
    except Exception as e:
        print(f"⚠️ Failed to fix triggers: {e}")
        print("Server will continue, but rating save may fail.\n")


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
app.include_router(activity_likes.router, prefix="/api/activity-likes", tags=["Activity Likes"])
app.include_router(comment_likes.router, prefix="/api/comment-likes", tags=["Comment Likes"])
app.include_router(user_posts.router, prefix="/api/user-posts", tags=["User Posts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
