"""
AniPass Backend Configuration
환경 설정 및 상수
"""
import os
from pathlib import Path

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
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")  # 프로덕션에서는 환경변수로 변경 필수
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# CORS Settings - Allow frontend domains
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,https://anipass.io,https://www.anipass.io"
).split(",")

# Add production origins if set
PRODUCTION_ORIGIN = os.getenv("PRODUCTION_ORIGIN")
if PRODUCTION_ORIGIN:
    ALLOWED_ORIGINS.append(PRODUCTION_ORIGIN)

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
# Set IMAGE_BASE_URL=https://images.anipass.io in production environment
