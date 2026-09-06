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
from api import auth, anime, ratings, reviews, comments, users, series, characters, character_ratings, feed, follows, activity_comments, comment_likes, user_posts, character_reviews, notifications, activities, rating_pages, admin_editor, bookmarks, search

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

# Startup is deliberately read-only. Release migrations are an explicit CLI job.
@app.on_event("startup")
async def startup_event():
    """Never mutate schema or user records during worker startup."""
    return None

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
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    from database import get_db
    from migrations import is_ready
    if not is_ready(get_db().db_path):
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


# Legacy image proxy removed - now using routers/image_proxy.py with auto-download functionality


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])  # Unified activities API
app.include_router(rating_pages.router, prefix="/api/rating-pages", tags=["Rating Pages"])  # Ultra-fast rating pages
app.include_router(anime.router, prefix="/api/anime", tags=["Anime"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])  # Unified search API
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


app.include_router(admin_editor.router, prefix="/api/admin/editor", tags=["Admin Editor"])



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
