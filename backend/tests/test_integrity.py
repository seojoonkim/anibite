import pytest
from fastapi import HTTPException
from models.rating import RatingCreate
from services.rating_service import create_or_update_rating
from services.character_service import create_or_update_character_rating


@pytest.mark.parametrize('kind',['anime','character'])
def test_rating_edit_preserves_social_references(populated,kind):
    db=populated
    def save(value):
        if kind=='anime':
            return create_or_update_rating(1,RatingCreate(anime_id=1,rating=value,status='RATED'))
        return create_or_update_character_rating(1,1,value,'RATED')
    save(4.0)
    activity=db.execute_query('SELECT * FROM activities',fetch_one=True)
    aid=activity['id']
    db.execute_insert('INSERT INTO activity_likes(activity_id,user_id) VALUES (?,2)',(aid,))
    db.execute_insert("INSERT INTO activity_comments(activity_id,user_id,content) VALUES (?,2,'keep')",(aid,))
    db.execute_insert('INSERT INTO activity_bookmarks(activity_id,user_id) VALUES (?,2)',(aid,))
    db.execute_insert("INSERT INTO notifications(activity_id,user_id,actor_id,type) VALUES (?,1,2,'like')",(aid,))
    save(4.5)
    assert db.execute_query('SELECT id,rating FROM activities',fetch_one=True)['id']==aid
    assert db.execute_query('SELECT rating FROM activities',fetch_one=True)[0]==4.5
    for table in ['activity_likes','activity_comments','activity_bookmarks','notifications']:
        assert db.execute_query(f'SELECT activity_id FROM {table}',fetch_one=True)[0]==aid
    assert db.execute_query('SELECT COUNT(*) FROM activities',fetch_one=True)[0]==1


def test_character_status_clears_rating(populated):
    create_or_update_character_rating(1,1,4.5,'RATED')
    result=create_or_update_character_rating(1,1,None,'WANT_TO_KNOW')
    assert result['rating'] is None


@pytest.mark.parametrize('rating,status',[(None,'RATED'),(4.2,'RATED'),(4,'UNKNOWN')])
def test_character_invalid_state_rejected(populated,rating,status):
    with pytest.raises((HTTPException, ValueError)):
        create_or_update_character_rating(1,1,rating,status)
    assert populated.execute_query('SELECT * FROM character_ratings')==[]


def test_rating_failure_rolls_back_source(populated):
    populated.execute_update("CREATE TRIGGER reject_projection BEFORE INSERT ON activities BEGIN SELECT RAISE(ABORT,'projection failure'); END")
    with pytest.raises(Exception,match='projection failure'):
        create_or_update_rating(1,RatingCreate(anime_id=1,rating=4,status='RATED'))
    assert populated.execute_query('SELECT * FROM user_ratings')==[]
