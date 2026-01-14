"""
Activity Service - Unified activity management

Handles all user activities (anime ratings/reviews, character ratings/reviews, user posts)
from a single 'activities' table.
"""
from typing import List, Optional, Dict
from database import Database, dict_from_row, db as default_db

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

    # Build WHERE clauses
    where_clauses = []
    params = []

    if activity_type:
        where_clauses.append("a.activity_type = ?")
        params.append(activity_type)

    if user_id:
        where_clauses.append("a.user_id = ?")
        params.append(user_id)

    if item_id and activity_type:
        where_clauses.append("a.item_id = ?")
        params.append(item_id)

    if following_only and current_user_id:
        where_clauses.append("""
            a.user_id IN (
                SELECT following_id FROM user_follows
                WHERE follower_id = ?
            )
        """)
        params.append(current_user_id)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_params = params.copy()
    total_row = db.execute_query(
        f"SELECT COUNT(*) as total FROM activities a WHERE {where_sql}",
        tuple(count_params),
        fetch_one=True
    )
    total = total_row['total'] if total_row else 0

    # Get activities with engagement counts
    # IMPORTANT: Parameters must be in the order they appear in the SQL!
    # Placeholders in SELECT come before WHERE in the SQL text
    query_params = []

    # Add current_user_id twice for liked check (FIRST in SQL)
    query_params.extend([current_user_id, current_user_id])

    # Add WHERE clause params (SECOND in SQL)
    query_params.extend(params)

    # Add limit and offset (LAST in SQL)
    query_params.extend([limit, offset])

    rows = db.execute_query(
        f"""
        SELECT
            a.*,
            COALESCE(us.otaku_score, a.otaku_score, 0) as otaku_score,
            (SELECT COUNT(*) FROM activity_likes al WHERE al.activity_id = a.id) as likes_count,
            (SELECT COUNT(*) FROM activity_comments ac WHERE ac.activity_id = a.id) as comments_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes al2
                 WHERE al2.activity_id = a.id AND al2.user_id = ?) > 0
            ELSE 0 END as user_liked
        FROM activities a
        LEFT JOIN user_stats us ON a.user_id = us.user_id
        WHERE {where_sql}
        ORDER BY a.activity_time DESC
        LIMIT ? OFFSET ?
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
        items.append(activity_dict)

    return {
        'items': items,
        'total': total
    }


def get_activity_by_id(activity_id: int, current_user_id: Optional[int] = None, db: Database = None) -> Optional[Dict]:
    """Get a single activity by ID"""

    if db is None:
        db = default_db

    # ALWAYS add current_user_id twice (even if None) to match SQL placeholders, then activity_id
    query_params = [current_user_id, current_user_id, activity_id]

    row = db.execute_query(
        """
        SELECT
            a.*,
            COALESCE(us.otaku_score, a.otaku_score, 0) as otaku_score,
            (SELECT COUNT(*) FROM activity_likes al WHERE al.activity_id = a.id) as likes_count,
            (SELECT COUNT(*) FROM activity_comments ac WHERE ac.activity_id = a.id) as comments_count,
            CASE WHEN ? IS NOT NULL THEN
                (SELECT COUNT(*) FROM activity_likes al2
                 WHERE al2.activity_id = a.id AND al2.user_id = ?) > 0
            ELSE 0 END as user_liked
        FROM activities a
        LEFT JOIN user_stats us ON a.user_id = us.user_id
        WHERE a.id = ?
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

    # Insert activity
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
    """
    db = default_db

    # Verify ownership
    activity = get_activity_by_id(activity_id, user_id)
    if not activity or activity['user_id'] != user_id:
        return None

    # Build update query
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

    return get_activity_by_id(activity_id, user_id)


def delete_activity(activity_id: int, user_id: int) -> bool:
    """
    Delete an activity

    Note: For anime/character ratings, delete the source rating (triggers will sync)
    This is mainly for user_posts.
    """
    db = default_db

    # Verify ownership
    activity = get_activity_by_id(activity_id, user_id)
    if not activity or activity['user_id'] != user_id:
        return False

    # Delete related comments
    db.execute_update(
        "DELETE FROM activity_comments WHERE activity_id = ?",
        (activity_id,)
    )

    # Delete related likes
    db.execute_update(
        "DELETE FROM activity_likes WHERE activity_id = ?",
        (activity_id,)
    )

    # Delete activity
    rowcount = db.execute_update(
        "DELETE FROM activities WHERE id = ? AND user_id = ?",
        (activity_id, user_id)
    )

    return rowcount > 0


def like_activity(activity_id: int, user_id: int) -> bool:
    """Like an activity"""
    db = default_db

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
        return False
    else:
        # Not liked, add like
        db.execute_insert(
            "INSERT INTO activity_likes (activity_id, user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (activity_id, user_id)
        )
        return True


def get_activity_comments(activity_id: int) -> List[Dict]:
    """Get comments for an activity"""
    db = default_db

    # Get top-level comments
    rows = db.execute_query(
        """
        SELECT
            ac.id, ac.activity_id, ac.user_id, ac.content, ac.created_at, ac.parent_comment_id,
            u.username, u.display_name, u.avatar_url,
            COALESCE(us.otaku_score, 0) as otaku_score
        FROM activity_comments ac
        JOIN users u ON ac.user_id = u.id
        LEFT JOIN user_stats us ON u.id = us.user_id
        WHERE ac.activity_id = ? AND ac.parent_comment_id IS NULL
        ORDER BY ac.created_at ASC
        """,
        (activity_id,)
    )

    comments = [dict_from_row(row) for row in rows]

    # Get replies for each comment
    for comment in comments:
        reply_rows = db.execute_query(
            """
            SELECT
                ac.id, ac.activity_id, ac.user_id, ac.content, ac.created_at, ac.parent_comment_id,
                u.username, u.display_name, u.avatar_url,
                COALESCE(us.otaku_score, 0) as otaku_score
            FROM activity_comments ac
            JOIN users u ON ac.user_id = u.id
            LEFT JOIN user_stats us ON u.id = us.user_id
            WHERE ac.parent_comment_id = ?
            ORDER BY ac.created_at ASC
            """,
            (comment['id'],)
        )
        comment['replies'] = [dict_from_row(row) for row in reply_rows]

    return comments


def create_activity_comment(
    activity_id: int,
    user_id: int,
    content: str,
    parent_comment_id: Optional[int] = None
) -> Dict:
    """Create a comment on an activity"""
    db = default_db

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

    # Verify comment exists and user is the author
    comment = db.execute_query(
        "SELECT id FROM activity_comments WHERE id = ? AND user_id = ?",
        (comment_id, user_id),
        fetch_one=True
    )

    if not comment:
        return False

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

    return rowcount > 0
