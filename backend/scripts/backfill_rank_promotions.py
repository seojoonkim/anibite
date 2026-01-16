"""
Backfill rank promotion activities for existing users

이 스크립트는 과거의 모든 승급 시점을 찾아서 activities 테이블에 추가합니다.
각 사용자의 평가/리뷰 활동을 시간순으로 추적하면서 랭크 변경을 감지합니다.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'anime.db')


def get_rank_info(otaku_score: float) -> tuple:
    """Get rank name and level from otaku score"""
    if otaku_score < 10:
        return "캐주얼", 1
    elif otaku_score < 25:
        return "캐주얼", 2
    elif otaku_score < 50:
        return "초보", 1
    elif otaku_score < 100:
        return "초보", 2
    elif otaku_score < 150:
        return "초보", 3
    elif otaku_score < 200:
        return "입문", 1
    elif otaku_score < 250:
        return "입문", 2
    elif otaku_score < 300:
        return "입문", 3
    elif otaku_score < 400:
        return "중급", 1
    elif otaku_score < 500:
        return "중급", 2
    elif otaku_score < 600:
        return "중급", 3
    elif otaku_score < 700:
        return "마스터", 1
    elif otaku_score < 800:
        return "마스터", 2
    elif otaku_score < 900:
        return "마스터", 3
    elif otaku_score < 1000:
        return "마스터", 4
    elif otaku_score < 1100:
        return "마스터", 5
    elif otaku_score < 1300:
        return "하이마스터", 1
    elif otaku_score < 1500:
        return "하이마스터", 2
    elif otaku_score < 1700:
        return "하이마스터", 3
    elif otaku_score < 1900:
        return "하이마스터", 4
    elif otaku_score < 2100:
        return "하이마스터", 5
    elif otaku_score < 2300:
        return "하이마스터", 6
    elif otaku_score < 2600:
        return "그랜드마스터", 1
    elif otaku_score < 2900:
        return "그랜드마스터", 2
    elif otaku_score < 3200:
        return "그랜드마스터", 3
    elif otaku_score < 3500:
        return "그랜드마스터", 4
    elif otaku_score < 3800:
        return "그랜드마스터", 5
    elif otaku_score < 4100:
        return "그랜드마스터", 6
    elif otaku_score < 4400:
        return "그랜드마스터", 7
    else:
        return "레전드", 1


def backfill_rank_promotions():
    """모든 사용자의 과거 승급 이력을 찾아서 activities에 추가"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all users
        users = cursor.execute("SELECT id, username, display_name, avatar_url FROM users").fetchall()

        total_promotions = 0

        for user in users:
            user_id = user['id']
            username = user['username']
            display_name = user['display_name']
            avatar_url = user['avatar_url']

            print(f"\n처리 중: {display_name or username} (ID: {user_id})")

            # Get all activities for this user in chronological order
            activities = cursor.execute("""
                SELECT activity_time, activity_type
                FROM activities
                WHERE user_id = ? AND activity_type IN ('anime_rating', 'anime_review', 'character_rating', 'character_review')
                ORDER BY activity_time ASC
            """, (user_id,)).fetchall()

            # Calculate otaku_score at each point in time
            anime_ratings_count = 0
            character_ratings_count = 0
            reviews_count = 0

            prev_rank = None
            prev_level = None

            for activity in activities:
                activity_time = activity['activity_time']
                activity_type = activity['activity_type']

                # Update counts based on activity type
                if activity_type == 'anime_rating':
                    anime_ratings_count += 1
                elif activity_type == 'character_rating':
                    character_ratings_count += 1
                elif activity_type in ('anime_review', 'character_review'):
                    reviews_count += 1

                # Calculate current otaku_score
                otaku_score = (anime_ratings_count * 2) + (character_ratings_count * 1) + (reviews_count * 5)

                # Get current rank
                current_rank, current_level = get_rank_info(otaku_score)

                # Check if rank changed
                if prev_rank is not None:
                    if (current_rank != prev_rank) or (current_rank == prev_rank and current_level > prev_level):
                        # Rank promotion detected!
                        print(f"  승급 발견: {prev_rank}-{prev_level} → {current_rank}-{current_level} (점수: {otaku_score}) at {activity_time}")

                        # Check if this promotion already exists
                        existing = cursor.execute("""
                            SELECT id FROM activities
                            WHERE activity_type = 'rank_promotion'
                              AND user_id = ?
                              AND activity_time = ?
                        """, (user_id, activity_time)).fetchone()

                        if not existing:
                            # Create metadata
                            metadata = json.dumps({
                                'old_rank': prev_rank,
                                'old_level': prev_level,
                                'new_rank': current_rank,
                                'new_level': current_level,
                                'otaku_score': otaku_score
                            })

                            # Insert rank promotion activity
                            cursor.execute("""
                                INSERT INTO activities (
                                    activity_type, user_id, username, display_name, avatar_url,
                                    item_id, metadata, activity_time, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                'rank_promotion',
                                user_id,
                                username,
                                display_name,
                                avatar_url,
                                None,
                                metadata,
                                activity_time,
                                datetime.now().isoformat(),
                                datetime.now().isoformat()
                            ))

                            total_promotions += 1

                # Update previous rank
                prev_rank = current_rank
                prev_level = current_level

        # Commit all changes
        conn.commit()
        print(f"\n✅ 완료! 총 {total_promotions}개의 승급 활동을 추가했습니다.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류 발생: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    print("🎉 과거 승급 이력 백필 시작...\n")
    backfill_rank_promotions()
