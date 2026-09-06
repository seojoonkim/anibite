import pytest
from models.rating import RatingCreate, RatingStatus
from services.rating_service import create_or_update_rating, get_all_user_ratings, get_user_ratings


@pytest.mark.parametrize('status', ['WANT_TO_WATCH', 'PASS'])
def test_status_transition_removes_rating_from_projection_and_lists(populated, status):
    create_or_update_rating(1, RatingCreate(anime_id=1, rating=4, status='RATED'))
    aid = populated.execute_query('SELECT id FROM activities', fetch_one=True)[0]
    populated.execute_insert('INSERT INTO activity_likes(activity_id,user_id) VALUES (?,2)', (aid,))
    create_or_update_rating(1, RatingCreate(anime_id=1, status=status))
    activity = populated.execute_query('SELECT id,rating FROM activities', fetch_one=True)
    assert activity['id'] == aid and activity['rating'] is None
    assert get_all_user_ratings(1)['rated'] == []
    for without_review in (True, False):
        result = get_user_ratings(1, RatingStatus.RATED, without_review=without_review)
        assert result.items == [] and result.total == 0
    create_or_update_rating(1, RatingCreate(anime_id=1, rating=5, status='RATED'))
    assert populated.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid
    assert populated.execute_query('SELECT activity_id FROM activity_likes', fetch_one=True)[0] == aid
