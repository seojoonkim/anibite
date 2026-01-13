-- =====================================================
-- User Management Tables Migration
-- AniPass 애니메이션 평가 플랫폼
-- =====================================================

-- 사용자 정보
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 평점 (핵심 기능)
CREATE TABLE IF NOT EXISTS user_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    rating REAL CHECK(rating >= 0.5 AND rating <= 5.0 AND (rating * 2) = CAST(rating * 2 AS INTEGER)),  -- 0.5-5.0 in 0.5 increments
    status TEXT CHECK(status IN ('RATED', 'WANT_TO_WATCH', 'PASS')) DEFAULT 'RATED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, anime_id)
);

-- 사용자 리뷰 (선택적)
CREATE TABLE IF NOT EXISTS user_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    rating_id INTEGER REFERENCES user_ratings(id) ON DELETE CASCADE,
    title TEXT,
    content TEXT NOT NULL,
    is_spoiler BOOLEAN DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, anime_id)
);

-- 리뷰 좋아요
CREATE TABLE IF NOT EXISTS review_likes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_id INTEGER NOT NULL REFERENCES user_reviews(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, review_id)
);

-- 사용자 세션 (JWT 보조)
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,  -- UUID
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 추천 캐시 (성능 최적화)
CREATE TABLE IF NOT EXISTS recommendation_cache (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anime_id INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    predicted_rating REAL NOT NULL,
    confidence_score REAL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, anime_id)
);

-- 사용자 통계 (denormalized for performance)
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_rated INTEGER DEFAULT 0,
    total_want_to_watch INTEGER DEFAULT 0,
    total_pass INTEGER DEFAULT 0,
    average_rating REAL,
    total_reviews INTEGER DEFAULT 0,
    total_watch_time_minutes INTEGER DEFAULT 0,  -- 예상 시청 시간
    otaku_score REAL DEFAULT 0,  -- 오타쿠 점수
    favorite_genre TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 인덱스
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_anime ON user_ratings(anime_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_status ON user_ratings(status);
CREATE INDEX IF NOT EXISTS idx_user_ratings_rating ON user_ratings(rating DESC);
CREATE INDEX IF NOT EXISTS idx_user_ratings_created ON user_ratings(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_reviews_user ON user_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_user_reviews_anime ON user_reviews(anime_id);
CREATE INDEX IF NOT EXISTS idx_user_reviews_likes ON user_reviews(likes_count DESC);

CREATE INDEX IF NOT EXISTS idx_recommendation_cache_user ON recommendation_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_cache_score ON recommendation_cache(predicted_rating DESC);
CREATE INDEX IF NOT EXISTS idx_recommendation_cache_generated ON recommendation_cache(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);

-- =====================================================
-- 마이그레이션 메타 정보
-- =====================================================

CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO migration_history (version, description)
VALUES ('001', 'Add user management tables for rating and review system');
