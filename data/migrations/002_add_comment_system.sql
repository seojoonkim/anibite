-- =====================================================
-- Comment System Migration (Phase 1)
-- 리뷰 댓글 + 대댓글 (2 depth) + 댓글 좋아요
-- =====================================================

-- 리뷰 댓글 (확장 가능한 구조)
CREATE TABLE IF NOT EXISTS review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_id INTEGER NOT NULL,  -- user_reviews.id (Phase 1), 나중에 다른 리뷰 타입도 지원
    review_type TEXT NOT NULL CHECK(review_type IN (
        'anime',           -- Phase 1: 애니메이션 리뷰
        'anime_aspect',    -- Phase 2: 세부 항목 리뷰
        'character',       -- Phase 3: 캐릭터 리뷰
        'staff'            -- Phase 4: 성우/스태프 리뷰
    )) DEFAULT 'anime',
    parent_comment_id INTEGER REFERENCES review_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK(LENGTH(content) >= 1 AND LENGTH(content) <= 1000),
    likes_count INTEGER DEFAULT 0,
    depth INTEGER DEFAULT 1 CHECK(depth IN (1, 2)),  -- 1: 댓글, 2: 대댓글
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 댓글 좋아요
CREATE TABLE IF NOT EXISTS comment_likes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment_id INTEGER NOT NULL REFERENCES review_comments(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, comment_id)
);

-- =====================================================
-- 인덱스
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_review_comments_review ON review_comments(review_id, review_type);
CREATE INDEX IF NOT EXISTS idx_review_comments_user ON review_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_review_comments_parent ON review_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_review_comments_created ON review_comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_review_comments_likes ON review_comments(likes_count DESC);

CREATE INDEX IF NOT EXISTS idx_comment_likes_comment ON comment_likes(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_likes_user ON comment_likes(user_id);

-- =====================================================
-- Triggers
-- =====================================================

-- 1. 대댓글 depth 자동 설정 및 검증
CREATE TRIGGER IF NOT EXISTS set_comment_depth
BEFORE INSERT ON review_comments
FOR EACH ROW
WHEN NEW.parent_comment_id IS NOT NULL
BEGIN
    -- 부모 댓글의 depth가 2인 경우 에러 발생
    SELECT CASE
        WHEN (SELECT depth FROM review_comments WHERE id = NEW.parent_comment_id) = 2
        THEN RAISE(ABORT, 'Cannot reply to a reply - maximum depth is 2')
    END;

    -- depth를 2로 업데이트
    UPDATE review_comments SET depth = 2 WHERE id = NEW.id;
END;

-- 2. 댓글 좋아요 추가 시 likes_count 증가
CREATE TRIGGER IF NOT EXISTS increment_comment_likes
AFTER INSERT ON comment_likes
FOR EACH ROW
BEGIN
    UPDATE review_comments
    SET likes_count = likes_count + 1
    WHERE id = NEW.comment_id;
END;

-- 3. 댓글 좋아요 삭제 시 likes_count 감소
CREATE TRIGGER IF NOT EXISTS decrement_comment_likes
AFTER DELETE ON comment_likes
FOR EACH ROW
BEGIN
    UPDATE review_comments
    SET likes_count = likes_count - 1
    WHERE id = OLD.comment_id;
END;

-- 4. 댓글 수정 시 updated_at 자동 갱신
CREATE TRIGGER IF NOT EXISTS update_comment_timestamp
AFTER UPDATE ON review_comments
FOR EACH ROW
BEGIN
    UPDATE review_comments
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- =====================================================
-- 마이그레이션 기록
-- =====================================================

INSERT OR IGNORE INTO migration_history (version, description)
VALUES ('002', 'Add comment system with 2-depth replies and likes');
