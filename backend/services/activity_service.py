"""
Activity Service - Unified activity management

Handles all user activities (anime ratings/reviews, character ratings/reviews, user posts)
from a single 'activities' table.

NORMALIZED: Item titles and images are fetched via JOIN, not stored in activities table.
"""
from typing import List, Optional, Dict
from database import Database, dict_from_row, db as default_db
from api.notifications import create_notification, delete_notification_by_action

# Retained empty projections keep social identity but are not public content.
VISIBLE_ACTIVITY_SQL = "(a.activity_type NOT IN ('anime_rating','character_rating','anime_review','character_review','user_post') OR a.rating IS NOT NULL OR NULLIF(TRIM(a.review_content), '') IS NOT NULL)"


def get_activities(
    db: Database,
    activity_type: Optional[str] = None,
    user_id: Optional[int] = None,
    item_id: Optional[int] = None,
    following_only: bool = False,
    current_user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict:
    """
    Get activities with optional filtering

    Args:
        activity_type: Filter by type ('anime_rating', 'character_rating', 'user_post')
        user_id: Filter by user
        item_id: Filter by item (anime_id or character_id)
        following_only: Show only activities from followed users
        current_user_id: Current user for liked status
        limit: Number of results
        offset: Pagination offset

    Returns:
        Dict with 'items' (list of activities) and 'total' (count)
    """

    # Build WHERE clauses and JOIN clauses
    where_clauses = [VISIBLE_ACTIVITY_SQL]
    params = []

    # Build JOIN clause for following_only filter (more efficient than subquery)
    follow_join = ""
    if following_only and current_user_id:
        follow_join = "INNER JOIN user_follows uf ON uf.following_id = a.user_id AND uf.follower_id = ?"
        params.append(current_user_id)

    if activity_type:
        where_clauses.append("a.activity_type = ?")
        params.append(activity_type)

    if user_id:
        where_clauses.append("a.user_id = ?")
        params.append(user_id)

    if item_id and activity_type:
        where_clauses.append("a.item_id = ?")
        params.append(item_id)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_params = params.copy()
    total_row = db.execute_query(
        f"SELECT COUNT(*) as total FROM activities a {follow_join} WHERE {where_sql}",
        tuple(count_params),
        fetch_one=True
    )
    total = total_row['total'] if total_row else 0

    # Get activities with engagement counts
    # NORMALIZED: JOIN anime/character tables to get titles dynamically
    query_params = [*params, limit, offset, current_user_id, current_user_id]

    rows = db.execute_query(
        f"""
        WITH page AS MATERIALIZED (
            SELECT a.* FROM activities a {follow_join} WHERE {where_sql}
            ORDER BY a.activity_time DESC,a.id DESC LIMIT ? OFFSET ?
        )
        SELECT
            a.id,
            a.activity_type,
            a.user_id,
            a.username,
            a.display_name,
            a.avatar_url,
            COALESCE(us.otaku_score, a.otaku_score, 0) as otaku_score,
            a.item_id,
            -- Item title: from anime or character table based on activity_type
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_romaji
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_full
                ELSE a.item_title
            END as item_title,
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_korean
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_korean
                ELSE a.item_title_korean
            END as item_title_korean,
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_native
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_native
                ELSE a.item_title_native
            END as item_title_native,
            -- Item image: from anime or character table
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN COALESCE('/' || an.cover_image_local, an.cover_image_url)
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN COALESCE(ch.image_local, ch.image_url)
                ELSE a.item_image
            END as item_image,
            a.rating,
            a.review_title,
            a.review_content,
            a.is_spoiler,
            -- For character activities: anime info from anime_id stored in activities table
            a.anime_id as anime_id,
            a.anime_title as anime_title,
            a.anime_title_korean as anime_title_korean,
            a.anime_title_native as anime_title_native,
            a.metadata,
            COALESCE(likes.count, 0) as likes_count,
            COALESCE(comments.count, 0) as comments_count,
            CASE WHEN ? IS NOT NULL AND user_like.activity_id IS NOT NULL THEN 1 ELSE 0 END as user_liked,
            a.activity_time,
            a.created_at,
            a.updated_at
        FROM page a
        -- JOIN anime table for anime activities
        LEFT JOIN anime an ON a.activity_type IN ('anime_rating', 'anime_review') AND a.item_id = an.id
        -- JOIN character table for character activities
        LEFT JOIN character ch ON a.activity_type IN ('character_rating', 'character_review') AND a.item_id = ch.id
        -- User stats
        LEFT JOIN user_stats us ON a.user_id = us.user_id
        -- Engagement counts
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_likes WHERE activity_id IN (SELECT id FROM page)
            GROUP BY activity_id
        ) likes ON likes.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_comments WHERE activity_id IN (SELECT id FROM page)
            GROUP BY activity_id
        ) comments ON comments.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id
            FROM activity_likes
            WHERE user_id = ?
        ) user_like ON user_like.activity_id = a.id
        ORDER BY a.activity_time DESC,a.id DESC
        """,
        tuple(query_params)
    )

    items = []
    for row in rows:
        activity_dict = dict_from_row(row)
        # Convert user_liked to boolean
        activity_dict['user_liked'] = bool(activity_dict.get('user_liked', 0))
        # Add is_my_activity flag
        if current_user_id:
            activity_dict['is_my_activity'] = activity_dict['user_id'] == current_user_id
        else:
            activity_dict['is_my_activity'] = False

        # Parse metadata JSON strings (for rank_promotion)
        if activity_dict.get('metadata') and isinstance(activity_dict['metadata'], str):
            try:
                import json
                activity_dict['metadata'] = json.loads(activity_dict['metadata'])
            except (json.JSONDecodeError, TypeError):
                activity_dict['metadata'] = None

        items.append(activity_dict)

    return {
        'items': items,
        'total': total
    }


def get_activity_by_id(activity_id: int, current_user_id: Optional[int] = None, db: Database = None) -> Optional[Dict]:
    """Get a single activity by ID with normalized JOINs"""

    if db is None:
        db = default_db

    # ALWAYS add current_user_id twice (even if None) to match SQL placeholders, then activity_id
    query_params = [current_user_id, current_user_id, activity_id]

    row = db.execute_query(
        f"""
        SELECT
            a.id,
            a.activity_type,
            a.user_id,
            a.username,
            a.display_name,
            a.avatar_url,
            COALESCE(us.otaku_score, a.otaku_score, 0) as otaku_score,
            a.item_id,
            -- Item title: from anime or character table based on activity_type
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_romaji
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_full
                ELSE a.item_title
            END as item_title,
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_korean
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_korean
                ELSE a.item_title_korean
            END as item_title_korean,
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN an.title_native
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN ch.name_native
                ELSE a.item_title_native
            END as item_title_native,
            -- Item image: from anime or character table
            CASE
                WHEN a.activity_type IN ('anime_rating', 'anime_review') THEN COALESCE('/' || an.cover_image_local, an.cover_image_url)
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN COALESCE(ch.image_local, ch.image_url)
                ELSE a.item_image
            END as item_image,
            a.rating,
            a.review_title,
            a.review_content,
            a.is_spoiler,
            -- For character activities: anime info from anime_character join
            CASE
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN char_anime.id
                ELSE NULL
            END as anime_id,
            CASE
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN char_anime.title_romaji
                ELSE NULL
            END as anime_title,
            CASE
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN char_anime.title_korean
                ELSE NULL
            END as anime_title_korean,
            CASE
                WHEN a.activity_type IN ('character_rating', 'character_review') THEN char_anime.title_native
                ELSE NULL
            END as anime_title_native,
            a.metadata,
            COALESCE(likes.count, 0) as likes_count,
            COALESCE(comments.count, 0) as comments_count,
            CASE WHEN ? IS NOT NULL AND user_like.activity_id IS NOT NULL THEN 1 ELSE 0 END as user_liked,
            a.activity_time,
            a.created_at,
            a.updated_at
        FROM activities a
        -- JOIN anime table for anime activities
        LEFT JOIN anime an ON a.activity_type IN ('anime_rating', 'anime_review') AND a.item_id = an.id
        -- JOIN character table for character activities
        LEFT JOIN character ch ON a.activity_type IN ('character_rating', 'character_review') AND a.item_id = ch.id
        -- JOIN anime_character to get the anime for character activities
        LEFT JOIN anime_character ac ON ch.id = ac.character_id AND ac.role = 'MAIN'
        LEFT JOIN anime char_anime ON ac.anime_id = char_anime.id
        -- User stats
        LEFT JOIN user_stats us ON a.user_id = us.user_id
        -- Engagement counts
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_likes
            GROUP BY activity_id
        ) likes ON likes.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id, COUNT(*) as count
            FROM activity_comments
            GROUP BY activity_id
        ) comments ON comments.activity_id = a.id
        LEFT JOIN (
            SELECT activity_id
            FROM activity_likes
            WHERE user_id = ?
        ) user_like ON user_like.activity_id = a.id
        WHERE a.id = ? AND {VISIBLE_ACTIVITY_SQL}
        """,
        tuple(query_params),
        fetch_one=True
    )

    if not row:
        return None

    activity_dict = dict_from_row(row)
    activity_dict['user_liked'] = bool(activity_dict.get('user_liked', 0))
    if current_user_id:
        activity_dict['is_my_activity'] = activity_dict['user_id'] == current_user_id
    else:
        activity_dict['is_my_activity'] = False

    # Parse metadata JSON strings (for rank_promotion)
    if activity_dict.get('metadata') and isinstance(activity_dict['metadata'], str):
        try:
            import json
            activity_dict['metadata'] = json.loads(activity_dict['metadata'])
        except (json.JSONDecodeError, TypeError):
            activity_dict['metadata'] = None

    return activity_dict


def create_activity(
    activity_type: str,
    user_id: int,
    item_id: Optional[int] = None,
    rating: Optional[float] = None,
    review_title: Optional[str] = None,
    review_content: Optional[str] = None,
    is_spoiler: bool = False
) -> Dict:
    """
    Create a new activity

    Note: Usually activities are created via triggers when ratings/reviews are created.
    This method is mainly for user_posts.
    """
    db = default_db

    # Get user info
    user = db.execute_query(
        """
        SELECT u.username, u.display_name, u.avatar_url, COALESCE(us.otaku_score, 0) as otaku_score
        FROM users u
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE u.id = ?
        """,
        (user_id,),
        fetch_one=True
    )

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Insert activity (no item_title etc - they will be JOINed on read)
    activity_id = db.execute_insert(
        """
        INSERT INTO activities (
            activity_type, user_id, item_id, activity_time,
            username, display_name, avatar_url, otaku_score,
            rating, review_title, review_content, is_spoiler
        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            activity_type, user_id, item_id,
            user['username'], user['display_name'], user['avatar_url'], user['otaku_score'],
            rating, review_title, review_content, is_spoiler
        )
    )

    return get_activity_by_id(activity_id, user_id)


@default_db.atomic
def update_activity(
    activity_id: int,
    user_id: int,
    review_title: Optional[str] = None,
    review_content: Optional[str] = None,
    is_spoiler: Optional[bool] = None
) -> Optional[Dict]:
    """
    Update activity review content

    Note: Rating updates should go through user_ratings table (triggers will sync)
    For user_posts, also updates the source user_posts table to maintain consistency
    """
    db = default_db

    # Verify ownership
    activity = get_activity_by_id(activity_id, user_id)
    if not activity or activity['user_id'] != user_id:
        return None

    if activity['activity_type'] in {'anime_rating','anime_review','character_rating','character_review'}:
        from services.projection_service import save_review
        kind='anime' if activity['activity_type'].startswith('anime') else 'character'
        save_review(kind,user_id,activity['item_id'],
                    review_title if review_title is not None else activity['review_title'],
                    review_content if review_content is not None else activity['review_content'],
                    is_spoiler if is_spoiler is not None else activity['is_spoiler'])
        return get_activity_by_id(activity_id,user_id)

    # Build update query for activities table
    updates = []
    params = []

    if review_title is not None:
        updates.append("review_title = ?")
        params.append(review_title)

    if review_content is not None:
        updates.append("review_content = ?")
        params.append(review_content)

    if is_spoiler is not None:
        updates.append("is_spoiler = ?")
        params.append(is_spoiler)

    if not updates:
        return activity

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(activity_id)

    db.execute_update(
        f"UPDATE activities SET {', '.join(updates)} WHERE id = ?",
        tuple(params)
    )

    # If this is a user_post, also update the source user_posts table
    if activity.get('activity_type') == 'user_post' and review_content is not None:
        item_id = activity.get('item_id')
        if item_id:
            db.execute_update(
                "UPDATE user_posts SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (review_content, item_id, user_id)
            )

    return get_activity_by_id(activity_id, user_id)


@default_db.atomic
def delete_activity(activity_id: int, user_id: int) -> bool:
    """Delete source content, retaining the hidden activity/social identity."""
    activity = get_activity_by_id(activity_id, user_id)
    if not activity or activity['user_id'] != user_id:
        return False
    item_id = activity['item_id']
    if activity['activity_type'] == 'user_post':
        from services.user_post_service import delete_post
        return delete_post(item_id, user_id)
    if activity['activity_type'] in {'anime_rating', 'character_rating'}:
        from services.projection_service import sources, sync_projection
        from services.rating_service import delete_rating
        from services.character_service import delete_character_rating
        from services.review_service import delete_review
        from services.character_review_service import delete_character_review
        kind = activity['activity_type'].split('_')[0]
        _, reviews, key, _ = sources(kind)
        review = default_db.execute_query(
            f'SELECT id FROM {reviews} WHERE user_id=? AND {key}=?', (user_id, item_id), fetch_one=True)
        if review:
            (delete_review if kind == 'anime' else delete_character_review)(review['id'], user_id)
        (delete_rating if kind == 'anime' else delete_character_rating)(user_id, item_id)
        sync_projection(kind, user_id, item_id)
        return True
    # Non-source events have no retained content identity.
    for table in ('activity_comments', 'activity_likes', 'activity_bookmarks', 'notifications'):
        default_db.execute_update(f'DELETE FROM {table} WHERE activity_id=?', (activity_id,))
    return default_db.execute_update('DELETE FROM activities WHERE id=? AND user_id=?', (activity_id, user_id)) > 0


@default_db.atomic
def like_activity(activity_id: int, user_id: int) -> bool:
    """Like an activity"""
    db = default_db

    # Get activity details for the required fields
    activity = db.execute_query(
        "SELECT activity_type, user_id as activity_user_id, item_id FROM activities WHERE id = ?",
        (activity_id,),
        fetch_one=True
    )

    if not activity:
        return False

    activity_type = activity[0]
    activity_user_id = activity[1]
    item_id = activity[2]

    # Check if already liked
    existing = db.execute_query(
        "SELECT 1 FROM activity_likes WHERE activity_id = ? AND user_id = ?",
        (activity_id, user_id),
        fetch_one=True
    )

    if existing:
        # Already liked, unlike
        db.execute_update(
            "DELETE FROM activity_likes WHERE activity_id = ? AND user_id = ?",
            (activity_id, user_id)
        )
        # Delete notification
        delete_notification_by_action(db, activity_user_id, user_id, 'like', activity_id)
        return False
    else:
        # Not liked, add like
        db.execute_insert(
            """INSERT INTO activity_likes
               (activity_id, user_id, activity_type, activity_user_id, item_id, created_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (activity_id, user_id, activity_type, activity_user_id, item_id)
        )
        # Create notification
        create_notification(db, activity_user_id, user_id, 'like', activity_id)
        return True


@default_db.atomic
def set_activity_like(activity_id: int, user_id: int, liked: bool) -> bool:
    """Idempotent explicit state; legacy POST toggle is retained separately."""
    db = default_db
    activity = db.execute_query('SELECT * FROM activities WHERE id=?',(activity_id,),fetch_one=True)
    if not activity:
        raise ValueError("Activity not found")
    if liked:
        changed = db.execute_update("""INSERT INTO activity_likes(activity_id,user_id,activity_type,activity_user_id,item_id)
            VALUES (?,?,?,?,?) ON CONFLICT(activity_id,user_id) DO NOTHING""",
            (activity_id,user_id,activity['activity_type'],activity['user_id'],activity['item_id']))
        if changed:
            create_notification(db,activity['user_id'],user_id,'like',activity_id)
    else:
        db.execute_update('DELETE FROM activity_likes WHERE activity_id=? AND user_id=?',(activity_id,user_id))
        delete_notification_by_action(db,activity['user_id'],user_id,'like',activity_id)
    return liked


def get_activity_comments(activity_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Two bounded queries; roots page independently, replies capped per root."""
    db = default_db
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    select = """SELECT ac.*, u.username,u.display_name,u.avatar_url,
        COALESCE(us.otaku_score,0) AS otaku_score FROM activity_comments ac
        JOIN users u ON u.id=ac.user_id LEFT JOIN user_stats us ON us.user_id=u.id"""
    roots = db.execute_query(select + """ WHERE ac.activity_id=? AND ac.parent_comment_id IS NULL
        ORDER BY ac.created_at,ac.id LIMIT ? OFFSET ?""",(activity_id,limit,offset))
    comments = [dict_from_row(row) for row in roots]
    if not comments:
        return []
    ids = [row['id'] for row in comments]
    placeholders = ','.join('?' for _ in ids)
    replies = db.execute_query(f"""WITH ranked AS (
        SELECT ac.*, ROW_NUMBER() OVER (PARTITION BY parent_comment_id ORDER BY created_at,id) AS rn,
        COUNT(*) OVER (PARTITION BY parent_comment_id) AS reply_total
        FROM activity_comments ac WHERE activity_id=? AND parent_comment_id IN ({placeholders})
    ) SELECT ac.*,u.username,u.display_name,u.avatar_url,COALESCE(us.otaku_score,0) AS otaku_score
      FROM ranked ac JOIN users u ON u.id=ac.user_id LEFT JOIN user_stats us ON us.user_id=u.id
      WHERE rn<=100 ORDER BY ac.created_at,ac.id""",(activity_id,*ids))
    grouped = {id: [] for id in ids}
    for row in replies:
        grouped[row['parent_comment_id']].append(dict_from_row(row))
    for comment in comments:
        comment['replies'] = grouped[comment['id']]
        comment['replies_has_more'] = bool(comment['replies'] and comment['replies'][0]['reply_total'] > 100)
    return comments


@default_db.atomic
def create_activity_comment(
    activity_id: int,
    user_id: int,
    content: str,
    parent_comment_id: Optional[int] = None
) -> Dict:
    """Create a comment on an activity"""
    db = default_db

    if not content or not content.strip() or len(content) > 1000:
        raise ValueError("Comment must contain 1–1000 characters")
    if parent_comment_id is not None:
        parent = db.execute_query('SELECT activity_id,parent_comment_id FROM activity_comments WHERE id=?', (parent_comment_id,), fetch_one=True)
        if not parent or parent['activity_id'] != activity_id:
            raise ValueError("Parent must belong to the same activity")
        if parent['parent_comment_id'] is not None:
            raise ValueError("Only one reply level is supported")

    # Verify activity exists and get activity info for legacy columns
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise ValueError(f"Activity {activity_id} not found")

    # Insert comment with legacy columns (activity_type, activity_user_id, item_id)
    comment_id = db.execute_insert(
        """
        INSERT INTO activity_comments (
            activity_id, user_id, parent_comment_id, content,
            activity_type, activity_user_id, item_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (activity_id, user_id, parent_comment_id, content,
         activity['activity_type'], activity['user_id'], activity.get('item_id'))
    )

    # Create notification for the activity owner
    create_notification(db, activity['user_id'], user_id, 'comment', activity_id, comment_id, content)

    # Get created comment
    comment = db.execute_query(
        """
        SELECT
            ac.id, ac.activity_id, ac.user_id, ac.content, ac.created_at, ac.parent_comment_id,
            u.username, u.display_name, u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM activity_comments ac
        JOIN users u ON ac.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE ac.id = ?
        """,
        (comment_id,),
        fetch_one=True
    )

    return dict_from_row(comment)


def delete_activity_comment(comment_id: int, user_id: int) -> bool:
    """Delete a comment (only by the author)"""
    db = default_db

    # Verify comment exists and get activity info for notification deletion
    comment = db.execute_query(
        "SELECT id, activity_id, activity_user_id FROM activity_comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id),
        fetch_one=True
    )

    if not comment:
        return False

    activity_id = comment[1]
    activity_user_id = comment[2]

    # Delete replies first (cascade)
    db.execute_update(
        "DELETE FROM activity_comments WHERE parent_comment_id = ?",
        (comment_id,)
    )

    # Delete the comment
    rowcount = db.execute_update(
        "DELETE FROM activity_comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id)
    )

    # Delete notification
    if rowcount > 0:
        delete_notification_by_action(db, activity_user_id, user_id, 'comment', activity_id)

    return rowcount > 0
