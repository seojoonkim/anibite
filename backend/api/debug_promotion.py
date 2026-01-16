"""
Debug API to find activities around rank promotions
승급 전후 활동 찾기
"""
from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter()


@router.get("/trace-promotion/{user_id}/{target_score}")
def trace_promotion(user_id: int, target_score: int):
    """
    Find the exact activity that triggered a promotion
    특정 점수(승급)를 트리거한 활동 찾기
    """

    # Get all activities in chronological order
    anime_ratings = db.execute_query(
        '''
        SELECT ur.updated_at, 'anime_rating', a.title_romaji, a.title_korean
        FROM user_ratings ur
        JOIN anime a ON ur.anime_id = a.id
        WHERE ur.user_id = ? AND ur.status = 'RATED'
        ORDER BY ur.updated_at ASC
        ''',
        (user_id,)
    )

    character_ratings = db.execute_query(
        '''
        SELECT cr.updated_at, 'character_rating', c.name_full, c.name_native
        FROM character_ratings cr
        JOIN character c ON cr.character_id = c.id
        WHERE cr.user_id = ?
        ORDER BY cr.updated_at ASC
        ''',
        (user_id,)
    )

    anime_reviews = db.execute_query(
        '''
        SELECT r.created_at, 'anime_review', a.title_romaji, a.title_korean
        FROM user_reviews r
        JOIN anime a ON r.anime_id = a.id
        WHERE r.user_id = ?
        ORDER BY r.created_at ASC
        ''',
        (user_id,)
    )

    character_reviews = db.execute_query(
        '''
        SELECT cr.created_at, 'character_review', c.name_full, c.name_native
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

    # Calculate cumulative score and find activities around target
    cumulative_anime = 0
    cumulative_char = 0
    cumulative_reviews = 0

    result = {
        'target_score': target_score,
        'activities_before': [],
        'trigger_activity': None,
        'activities_after': []
    }

    for i, activity in enumerate(activities):
        time, type_, title, title_kr = activity

        # Update counts
        if type_ == 'anime_rating':
            cumulative_anime += 1
        elif type_ == 'character_rating':
            cumulative_char += 1
        elif type_ in ['anime_review', 'character_review']:
            cumulative_reviews += 1

        score = cumulative_anime * 2 + cumulative_char * 1 + cumulative_reviews * 5

        activity_data = {
            'time': time,
            'type': type_,
            'title': title,
            'title_korean': title_kr,
            'score_after': score
        }

        # Find activities around target score
        if score < target_score - 10:
            continue
        elif score < target_score:
            result['activities_before'].append(activity_data)
        elif score == target_score:
            result['trigger_activity'] = activity_data
            result['trigger_activity']['anime_count'] = cumulative_anime
            result['trigger_activity']['char_count'] = cumulative_char
            result['trigger_activity']['review_count'] = cumulative_reviews
            # Add next few activities
            for j in range(i+1, min(i+4, len(activities))):
                next_act = activities[j]
                result['activities_after'].append({
                    'time': next_act[0],
                    'type': next_act[1],
                    'title': next_act[2],
                    'title_korean': next_act[3]
                })
            break
        elif score > target_score and not result['trigger_activity']:
            # We passed the target without hitting it exactly
            result['trigger_activity'] = activity_data
            result['trigger_activity']['anime_count'] = cumulative_anime
            result['trigger_activity']['char_count'] = cumulative_char
            result['trigger_activity']['review_count'] = cumulative_reviews
            result['note'] = f'Score jumped from {score - (2 if type_ == "anime_rating" else 1 if type_ == "character_rating" else 5)} to {score}'
            break

    return result
