"""
AniPass Backend Configuration
환경 설정 및 상수
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_PATH = BASE_DIR / "data" / "anime.db"

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")  # 프로덕션에서는 환경변수로 변경 필수
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://localhost:5174",  # Vite dev server (alternate port)
    "http://localhost:5175",  # Vite dev server (alternate port)
    "http://localhost:5176",  # Vite dev server (alternate port)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
]

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Rating constraints
MIN_RATING = 0.5
MAX_RATING = 5.0
RATING_INCREMENT = 0.5

# Comment constraints
MAX_COMMENT_LENGTH = 1000
MIN_COMMENT_LENGTH = 1
MAX_COMMENT_DEPTH = 2

# Review constraints
MAX_REVIEW_TITLE_LENGTH = 100
MAX_REVIEW_CONTENT_LENGTH = 5000
MIN_REVIEW_CONTENT_LENGTH = 10

# Recommendation settings
MIN_RATINGS_FOR_RECOMMENDATION = 10
RECOMMENDATION_CACHE_DAYS = 7
TOP_K_SIMILAR_USERS = 20

# Images
COVER_IMAGES_DIR = BASE_DIR / "data" / "images" / "covers"
