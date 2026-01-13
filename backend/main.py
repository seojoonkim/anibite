"""
AniPass Backend - FastAPI Application
왓챠피디아 스타일 애니메이션 평가 플랫폼
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import ALLOWED_ORIGINS, COVER_IMAGES_DIR
import os

# Import API routers
from api import auth, anime, ratings, reviews, comments, users, series, characters, feed, follows, activity_comments, activity_likes, comment_likes, user_posts, character_reviews, notifications

app = FastAPI(
    title="AniPass API",
    description="애니메이션 평가 및 추천 플랫폼 API",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to AniPass API",
        "docs": "/docs",
        "version": "1.0.0"
    }


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(anime.router, prefix="/api/anime", tags=["Anime"])
app.include_router(ratings.router, prefix="/api/ratings", tags=["Ratings"])
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
