CREATE TABLE IF NOT EXISTS character_ratings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, character_id INTEGER NOT NULL,
 rating REAL, status TEXT NOT NULL DEFAULT 'RATED',
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id, character_id),
 CHECK ((status = 'RATED' AND rating IS NOT NULL AND rating BETWEEN 0.5 AND 5 AND rating*2=CAST(rating*2 AS INTEGER)) OR (status IN ('WANT_TO_KNOW','NOT_INTERESTED') AND rating IS NULL))
);
CREATE TABLE IF NOT EXISTS character_reviews (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, character_id INTEGER NOT NULL,
 title TEXT, content TEXT NOT NULL, is_spoiler INTEGER DEFAULT 0, likes_count INTEGER DEFAULT 0,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,character_id)
);
CREATE TABLE IF NOT EXISTS activities (
 id INTEGER PRIMARY KEY AUTOINCREMENT, activity_type TEXT NOT NULL, user_id INTEGER NOT NULL,
 username TEXT NOT NULL, display_name TEXT, avatar_url TEXT, otaku_score REAL DEFAULT 0,
 item_id INTEGER, item_title TEXT, item_title_korean TEXT, item_title_native TEXT, item_image TEXT, item_year INTEGER,
 rating REAL, review_title TEXT, review_content TEXT, is_spoiler INTEGER DEFAULT 0,
 anime_id INTEGER, anime_title TEXT, anime_title_korean TEXT, anime_title_native TEXT, metadata TEXT,
 activity_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(activity_type,user_id,item_id)
);
CREATE TABLE IF NOT EXISTS activity_comments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, activity_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 parent_comment_id INTEGER, content TEXT NOT NULL, activity_type TEXT, activity_user_id INTEGER, item_id INTEGER,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS activity_likes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, activity_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 activity_type TEXT, activity_user_id INTEGER, item_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(activity_id,user_id)
);
CREATE TABLE IF NOT EXISTS activity_bookmarks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, activity_id INTEGER NOT NULL,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,activity_id)
);
CREATE TABLE IF NOT EXISTS notifications (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, actor_id INTEGER NOT NULL,
 type TEXT NOT NULL, activity_id INTEGER, comment_id INTEGER, content TEXT, is_read INTEGER DEFAULT 0,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, content TEXT NOT NULL,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_follows (
 follower_id INTEGER NOT NULL, following_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(follower_id,following_id)
);
CREATE TABLE IF NOT EXISTS review_comments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, review_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 parent_comment_id INTEGER, content TEXT NOT NULL, depth INTEGER DEFAULT 0,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS character_review_comments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, review_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 parent_comment_id INTEGER, content TEXT NOT NULL, depth INTEGER DEFAULT 0,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS comment_likes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, comment_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 comment_type TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(comment_id,user_id,comment_type)
);
CREATE TABLE IF NOT EXISTS character_review_likes (
 user_id INTEGER NOT NULL, review_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(user_id,review_id)
);
CREATE INDEX IF NOT EXISTS idx_activity_comments_page ON activity_comments(activity_id,created_at,id);
CREATE INDEX IF NOT EXISTS idx_activity_likes_page ON activity_likes(activity_id,user_id);
CREATE INDEX IF NOT EXISTS idx_activities_stable_page ON activities(activity_time DESC,id DESC);
