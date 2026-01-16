"""
Admin API for fixing rank promotions
관리자용 승급 메시지 수정 API
"""
from fastapi import APIRouter, HTTPException, Header
from database import db
import json
import os

router = APIRouter()


def get_rank_info(otaku_score):
    """Get rank name and level from otaku score"""
    if otaku_score < 50:
        return "루키", 1
    elif otaku_score < 120:
        return "헌터", 2
    elif otaku_score < 220:
        return "워리어", 3
    elif otaku_score < 350:
        return "나이트", 4
    elif otaku_score < 550:
        return "마스터", 5
    elif otaku_score < 800:
        return "하이마스터", 6
    elif otaku_score < 1100:
        return "그랜드마스터", 7
    elif otaku_score < 1450:
        return "오타쿠", 8
    elif otaku_score < 1800:
        return "오타쿠 킹", 9
    else:
        return "오타쿠 갓", 10


@router.post("/fix-promotions/{user_id}")
def fix_user_promotions(user_id: int, admin_key: str = Header(None)):
    """
    Fix rank promotions for a specific user
    관리자 전용: 승급 메시지를 올바른 시각으로 재생성
    """

    # Check admin key
    expected_key = os.getenv("ADMIN_KEY", "change-me-in-production")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    try:
        # Get user stats
        stats = db.execute_query(
            'SELECT total_rated, total_character_ratings, total_reviews, otaku_score FROM user_stats WHERE user_id = ?',
            (user_id,),
            fetch_one=True
        )

        if not stats:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete existing promotions
        db.execute_update(
            'DELETE FROM activities WHERE user_id = ? AND activity_type = "rank_promotion"',
            (user_id,)
        )

        # Get user info
        user_info = db.execute_query(
            'SELECT username, display_name, avatar_url FROM users WHERE id = ?',
            (user_id,),
            fetch_one=True
        )

        username, display_name, avatar_url = user_info[0], user_info[1], user_info[2]

        # Get all activities
        anime_ratings = db.execute_query(
            '''
            SELECT ur.updated_at, 'anime_rating', a.title_romaji
            FROM user_ratings ur
            JOIN anime a ON ur.anime_id = a.id
            WHERE ur.user_id = ? AND ur.status = 'RATED'
            ORDER BY ur.updated_at ASC
            ''',
            (user_id,)
        )

        character_ratings = db.execute_query(
            '''
            SELECT cr.updated_at, 'character_rating', c.name_full
            FROM character_ratings cr
            JOIN character c ON cr.character_id = c.id
            WHERE cr.user_id = ?
            ORDER BY cr.updated_at ASC
            ''',
            (user_id,)
        )

        anime_reviews = db.execute_query(
            '''
            SELECT r.created_at, 'anime_review', a.title_romaji
            FROM user_reviews r
            JOIN anime a ON r.anime_id = a.id
            WHERE r.user_id = ?
            ORDER BY r.created_at ASC
            ''',
            (user_id,)
        )

        character_reviews = db.execute_query(
            '''
            SELECT cr.created_at, 'character_review', c.name_full
            FROM character_reviews cr
            JOIN character c ON cr.character_id = c.id
            WHERE cr.user_id = ?
            ORDER BY cr.created_at ASC
            ''',
            (user_id,)
        )

        # Merge and sort
        activities = sorted(
            list(anime_ratings) + list(character_ratings) + list(anime_reviews) + list(character_reviews),
            key=lambda x: x[0]
        )

        # Calculate and generate promotions
        cumulative_anime = 0
        cumulative_char = 0
        cumulative_reviews = 0

        thresholds = [50, 120, 220, 350, 550, 800, 1100, 1450, 1800]
        generated = []

        for activity in activities:
            activity_time, activity_type, item_title = activity

            if activity_type == 'anime_rating':
                cumulative_anime += 1
            elif activity_type == 'character_rating':
                cumulative_char += 1
            elif activity_type in ['anime_review', 'character_review']:
                cumulative_reviews += 1

            current_score = (cumulative_anime * 2) + (cumulative_char * 1) + (cumulative_reviews * 5)

            for threshold in thresholds:
                if current_score >= threshold and threshold not in [g['threshold'] for g in generated]:
                    old_rank, old_level = get_rank_info(threshold - 1)
                    new_rank, new_level = get_rank_info(threshold)

                    metadata = json.dumps({
                        "old_rank": old_rank,
                        "old_level": old_level,
                        "new_rank": new_rank,
                        "new_level": new_level,
                        "otaku_score": current_score
                    })

                    db.execute_insert(
                        '''
                        INSERT INTO activities (
                            activity_type, user_id, username, display_name, avatar_url,
                            item_id, metadata, activity_time, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''',
                        (
                            'rank_promotion',
                            user_id,
                            username,
                            display_name,
                            avatar_url,
                            None,
                            metadata,
                            activity_time
                        )
                    )

                    generated.append({
                        'threshold': threshold,
                        'level': new_level,
                        'rank': new_rank,
                        'time': activity_time
                    })

        return {
            'success': True,
            'user_id': user_id,
            'stats': {
                'anime_ratings': stats[0],
                'character_ratings': stats[1],
                'total_reviews': stats[2],
                'otaku_score': stats[3]
            },
            'promotions_generated': len(generated),
            'promotions': generated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fix promotions: {str(e)}")
