"""
AniPass Backend Configuration
환경 설정 및 상수
"""
import os
from pathlib import Path
import secrets

# Configuration comes only from the process environment; never discover .env.

# Base directory
# In production (Railway), we work from backend/ directory
# In development, we might work from project root
BASE_DIR = Path(__file__).resolve().parent
# Check if we're in backend/ directory, if so use parent for data access
if BASE_DIR.name == "backend":
    DATA_DIR = BASE_DIR.parent / "data"
else:
    DATA_DIR = BASE_DIR / "data"

# Database - 단일 DB 구조 (볼륨에 영구 저장)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "anime.db"))

# JWT Settings
APP_ENV = os.getenv("APP_ENV", "production").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production" or len(SECRET_KEY) < 32:
    if APP_ENV not in {"development", "test"}:
        raise RuntimeError("SECRET_KEY must be explicitly configured with at least 32 characters")
    # Explicit development only: ephemeral keys invalidate tokens on restart.
    SECRET_KEY = secrets.token_urlsafe(48)
ADMIN_USER_IDS = frozenset(int(value.strip()) for value in os.getenv("ADMIN_USER_IDS", "").split(",") if value.strip())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Google OAuth Settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# CORS Settings - Allow frontend domains
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
]

# Production origins - always included
_PRODUCTION_ORIGINS = [
    "https://anibite.com",
    "https://www.anibite.com",
]

# Build allowed origins list
_env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
ALLOWED_ORIGINS = list(set(_DEFAULT_ORIGINS + _PRODUCTION_ORIGINS + [o.strip() for o in _env_origins if o.strip()]))

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
COVER_IMAGES_DIR = DATA_DIR / "images" / "covers"
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "http://localhost:8000/images")

# Cloudflare R2 Settings (Production)
# Set IMAGE_BASE_URL=https://images.anibite.com in production environment
