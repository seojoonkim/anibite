#!/usr/bin/env python3
"""
Backfill notifications for existing likes and comments
기존 좋아요와 댓글에 대한 알림 생성
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from api.notifications import create_notification

def backfill_like_notifications(db):
    """기존 좋아요에 대한 알림 생성"""
    print("\n" + "="*70)
    print("좋아요 알림 생성 중...")
    print("="*70)

    # Get all likes (excluding self-likes)
    likes = db.execute_query("""
        SELECT
            al.activity_id,
            al.user_id as liker_id,
            a.user_id as activity_owner_id,
            al.created_at
        FROM activity_likes al
        JOIN activities a ON al.activity_id = a.id
        WHERE al.user_id != a.user_id
        ORDER BY al.created_at DESC
    """)

    print(f"총 {len(likes)}개의 좋아요 발견")

    created = 0
    skipped = 0

    for like in likes:
        activity_id = like[0]
        liker_id = like[1]
        owner_id = like[2]
        created_at = like[3]

        # Check if notification already exists
        existing = db.execute_query("""
            SELECT id FROM notifications
            WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = 'like'
        """, (owner_id, liker_id, activity_id), fetch_one=True)

        if existing:
            skipped += 1
            continue

        # Create notification
        try:
            db.execute_insert("""
                INSERT INTO notifications (user_id, actor_id, type, activity_id, created_at)
                VALUES (?, ?, 'like', ?, ?)
            """, (owner_id, liker_id, activity_id, created_at))
            created += 1

            if created % 10 == 0:
                print(f"  {created}개 생성 완료...")
        except Exception as e:
            print(f"  오류: {e}")

    print(f"\n✅ 좋아요 알림: {created}개 생성, {skipped}개 이미 존재")
    return created


def backfill_comment_notifications(db):
    """기존 댓글에 대한 알림 생성"""
    print("\n" + "="*70)
    print("댓글 알림 생성 중...")
    print("="*70)

    # Get all comments (excluding self-comments)
    comments = db.execute_query("""
        SELECT
            ac.id as comment_id,
            ac.activity_id,
            ac.user_id as commenter_id,
            a.user_id as activity_owner_id,
            ac.content,
            ac.created_at
        FROM activity_comments ac
        JOIN activities a ON ac.activity_id = a.id
        WHERE ac.user_id != a.user_id
        ORDER BY ac.created_at DESC
    """)

    print(f"총 {len(comments)}개의 댓글 발견")

    created = 0
    skipped = 0

    for comment in comments:
        comment_id = comment[0]
        activity_id = comment[1]
        commenter_id = comment[2]
        owner_id = comment[3]
        content = comment[4]
        created_at = comment[5]

        # Check if notification already exists
        existing = db.execute_query("""
            SELECT id FROM notifications
            WHERE user_id = ? AND actor_id = ? AND activity_id = ? AND type = 'comment'
        """, (owner_id, commenter_id, activity_id), fetch_one=True)

        if existing:
            skipped += 1
            continue

        # Create notification
        try:
            db.execute_insert("""
                INSERT INTO notifications (user_id, actor_id, type, activity_id, comment_id, content, created_at)
                VALUES (?, ?, 'comment', ?, ?, ?, ?)
            """, (owner_id, commenter_id, activity_id, comment_id, content, created_at))
            created += 1

            if created % 10 == 0:
                print(f"  {created}개 생성 완료...")
        except Exception as e:
            print(f"  오류: {e}")

    print(f"\n✅ 댓글 알림: {created}개 생성, {skipped}개 이미 존재")
    return created


def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("알림 백필 시작")
    print("="*70)

    db = get_db()

    # Backfill likes
    likes_created = backfill_like_notifications(db)

    # Backfill comments
    comments_created = backfill_comment_notifications(db)

    print("\n" + "="*70)
    print("백필 완료!")
    print("="*70)
    print(f"총 {likes_created + comments_created}개의 알림 생성")
    print(f"  - 좋아요 알림: {likes_created}개")
    print(f"  - 댓글 알림: {comments_created}개")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
