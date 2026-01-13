"""
캐릭터 평가/리뷰 댓글 통합 마이그레이션 스크립트
activity_comments의 character_rating 댓글을 review_comments로 이동
"""
from database import Database

def migrate_character_comments():
    db = Database()

    print("=== 캐릭터 댓글 마이그레이션 시작 ===\n")

    # 1. 현재 상태 확인
    activity_comments_count = db.execute_query(
        "SELECT COUNT(*) FROM activity_comments WHERE activity_type = 'character_rating'",
        fetch_one=True
    )[0]

    review_comments_count = db.execute_query(
        "SELECT COUNT(*) FROM review_comments WHERE review_type = 'character'",
        fetch_one=True
    )[0]

    print(f"마이그레이션 전:")
    print(f"  activity_comments (character_rating): {activity_comments_count}개")
    print(f"  review_comments (character): {review_comments_count}개\n")

    # 2. activity_comments에서 character_rating 댓글 가져오기
    activity_comments = db.execute_query("""
        SELECT
            id,
            user_id,
            activity_user_id,
            item_id as character_id,
            content,
            parent_comment_id,
            created_at
        FROM activity_comments
        WHERE activity_type = 'character_rating'
        ORDER BY created_at ASC
    """)

    if not activity_comments:
        print("마이그레이션할 댓글이 없습니다.")
        return

    print(f"마이그레이션할 댓글: {len(activity_comments)}개\n")

    # 3. 각 댓글에 대해 처리
    migrated_count = 0
    error_count = 0

    for comment in activity_comments:
        comment_id = comment[0]
        user_id = comment[1]
        activity_user_id = comment[2]
        character_id = comment[3]
        content = comment[4]
        parent_comment_id = comment[5]
        created_at = comment[6]

        try:
            # 3-1. 해당 캐릭터에 리뷰가 있는지 확인
            review = db.execute_query(
                "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                (activity_user_id, character_id),
                fetch_one=True
            )

            review_id = None
            if review:
                review_id = review['id']
                print(f"  댓글 {comment_id}: 기존 리뷰 {review_id} 사용")
            else:
                # 3-2. 리뷰가 없으면 빈 리뷰 생성
                # 먼저 평가가 있는지 확인
                rating = db.execute_query(
                    "SELECT rating FROM character_ratings WHERE user_id = ? AND character_id = ?",
                    (activity_user_id, character_id),
                    fetch_one=True
                )

                if not rating:
                    print(f"  댓글 {comment_id}: 평가가 없어 스킵")
                    error_count += 1
                    continue

                # 빈 리뷰 생성 (content가 빈 문자열인 리뷰)
                db.execute_query("""
                    INSERT INTO character_reviews
                    (user_id, character_id, content, title, is_spoiler, likes_count, created_at, updated_at)
                    VALUES (?, ?, '', NULL, 0, 0, ?, ?)
                """, (activity_user_id, character_id, created_at, created_at))

                review = db.execute_query(
                    "SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                    (activity_user_id, character_id),
                    fetch_one=True
                )
                review_id = review['id']
                print(f"  댓글 {comment_id}: 새 리뷰 {review_id} 생성")

            # 3-3. parent_comment_id 매핑 (activity_comments의 parent가 있으면 변환 필요)
            new_parent_id = None
            if parent_comment_id:
                # 부모 댓글이 이미 마이그레이션되었는지 확인
                parent_mapping = db.execute_query(
                    "SELECT id FROM review_comments WHERE review_type = 'character' AND review_id = ? AND content = (SELECT content FROM activity_comments WHERE id = ?)",
                    (review_id, parent_comment_id),
                    fetch_one=True
                )
                if parent_mapping:
                    new_parent_id = parent_mapping['id']

            # 3-4. 이미 review_comments에 같은 댓글이 있는지 확인 (중복 방지)
            existing = db.execute_query(
                "SELECT id FROM review_comments WHERE review_id = ? AND user_id = ? AND content = ? AND created_at = ?",
                (review_id, user_id, content, created_at),
                fetch_one=True
            )

            if existing:
                print(f"  댓글 {comment_id}: 이미 존재함, 스킵")
                continue

            # 3-5. review_comments에 댓글 추가
            db.execute_query("""
                INSERT INTO review_comments
                (review_id, review_type, user_id, content, parent_comment_id, created_at)
                VALUES (?, 'character', ?, ?, ?, ?)
            """, (review_id, user_id, content, new_parent_id, created_at))

            migrated_count += 1
            print(f"  댓글 {comment_id}: 마이그레이션 완료 → review_comments")

        except Exception as e:
            print(f"  댓글 {comment_id}: 에러 발생 - {e}")
            error_count += 1

    # 4. 마이그레이션 후 상태 확인
    new_review_comments_count = db.execute_query(
        "SELECT COUNT(*) FROM review_comments WHERE review_type = 'character'",
        fetch_one=True
    )[0]

    print(f"\n마이그레이션 완료:")
    print(f"  성공: {migrated_count}개")
    print(f"  실패/스킵: {error_count}개")
    print(f"  review_comments (character): {new_review_comments_count}개")

    # 5. activity_comments 삭제 확인
    print(f"\n주의: activity_comments의 character_rating 댓글은 수동으로 삭제해야 합니다.")
    print(f"  확인 후 실행: DELETE FROM activity_comments WHERE activity_type = 'character_rating'")

if __name__ == "__main__":
    migrate_character_comments()
