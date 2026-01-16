"""Migrate existing likes and comments to notifications table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def migrate_notifications():
    db = get_db()

    print("Starting migration to notifications table...")

    # 1. Migrate likes
    print("\n1. Migrating likes...")
    likes_query = """
    SELECT
        al.user_id as actor_id,
        a.user_id as target_user_id,
        al.activity_id,
        al.created_at
    FROM activity_likes al
    JOIN activities a ON al.activity_id = a.id
    WHERE al.user_id != a.user_id
    """

    likes = db.execute_query(likes_query)
    print(f"Found {len(likes)} likes to migrate")

    likes_migrated = 0
    for like in likes:
        try:
            # Check if notification already exists
            existing = db.execute_query(
                """
                SELECT id FROM notifications
                WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = 'like'
                """,
                (like[1], like[0], like[2]),
                fetch_one=True
            )

            if not existing:
                db.execute_insert(
                    """
                    INSERT INTO notifications (user_id, actor_id, type, activity_id, created_at)
                    VALUES (?, ?, 'like', ?, ?)
                    """,
                    (like[1], like[0], like[2], like[3])
                )
                likes_migrated += 1
        except Exception as e:
            print(f"Error migrating like: {e}")

    print(f"✅ Migrated {likes_migrated} like notifications")

    # 2. Migrate comments
    print("\n2. Migrating comments...")
    comments_query = """
    SELECT
        ac.user_id as actor_id,
        a.user_id as target_user_id,
        ac.activity_id,
        ac.id as comment_id,
        ac.content,
        ac.created_at
    FROM activity_comments ac
    JOIN activities a ON ac.activity_id = a.id
    WHERE ac.user_id != a.user_id
        AND ac.parent_comment_id IS NULL
    """

    comments = db.execute_query(comments_query)
    print(f"Found {len(comments)} comments to migrate")

    comments_migrated = 0
    for comment in comments:
        try:
            # Check if notification already exists
            existing = db.execute_query(
                """
                SELECT id FROM notifications
                WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = 'comment'
                """,
                (comment[1], comment[0], comment[2]),
                fetch_one=True
            )

            if not existing:
                db.execute_insert(
                    """
                    INSERT INTO notifications (user_id, actor_id, type, activity_id, comment_id, content, created_at)
                    VALUES (?, ?, 'comment', ?, ?, ?, ?)
                    """,
                    (comment[1], comment[0], comment[2], comment[3], comment[4], comment[5])
                )
                comments_migrated += 1
        except Exception as e:
            print(f"Error migrating comment: {e}")

    print(f"✅ Migrated {comments_migrated} comment notifications")

    # Summary
    print(f"\n{'='*50}")
    print(f"Migration complete!")
    print(f"  - Like notifications: {likes_migrated}")
    print(f"  - Comment notifications: {comments_migrated}")
    print(f"  - Total: {likes_migrated + comments_migrated}")
    print(f"{'='*50}")

if __name__ == "__main__":
    migrate_notifications()
