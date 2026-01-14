-- Optimize following feed performance with indexes
-- These indexes will speed up the following feed queries

-- Index for user_follows table (following lookup)
CREATE INDEX IF NOT EXISTS idx_user_follows_follower
ON user_follows(follower_id, following_id);

-- Index for activities table (user_id lookup and sorting)
CREATE INDEX IF NOT EXISTS idx_activities_user_time
ON activities(user_id, activity_time DESC);

-- Index for activities table (activity_time for global feed)
CREATE INDEX IF NOT EXISTS idx_activities_time
ON activities(activity_time DESC);

-- Index for activity_likes (counting likes)
CREATE INDEX IF NOT EXISTS idx_activity_likes_activity
ON activity_likes(activity_id, user_id);

-- Index for activity_comments (counting comments)
CREATE INDEX IF NOT EXISTS idx_activity_comments_activity
ON activity_comments(activity_id);

-- Analyze tables to update query planner statistics
ANALYZE user_follows;
ANALYZE activities;
ANALYZE activity_likes;
ANALYZE activity_comments;
