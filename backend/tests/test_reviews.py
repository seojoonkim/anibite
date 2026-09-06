import pytest
from services import activity_service,review_service,character_review_service
from services.rating_service import create_or_update_rating
from services.character_service import create_or_update_character_rating
from models.rating import RatingCreate
from models.review import ReviewCreate
from models.character_review import CharacterReviewCreate

@pytest.mark.parametrize('kind',['anime','character'])
def test_review_writes_and_activity_edits_share_source(populated,kind):
    if kind=='anime':
        review_service.create_review(1,ReviewCreate(anime_id=1,rating=4,content='Original synthetic review'))
    else:
        character_review_service.create_character_review(1,CharacterReviewCreate(character_id=1,rating=4,content='Original synthetic review'))
    source='user_reviews' if kind=='anime' else 'character_reviews'
    a=populated.execute_query('SELECT * FROM activities',fetch_one=True)
    assert a and a['review_content']=='Original synthetic review' and a['rating']==4
    activity_service.update_activity(a['id'],1,review_content='Edited synthetic review')
    assert populated.execute_query(f'SELECT content FROM {source}',fetch_one=True)[0]=='Edited synthetic review'
    if kind=='anime':
        create_or_update_rating(1,RatingCreate(anime_id=1,rating=5,status='RATED'))
    else:
        create_or_update_character_rating(1,1,5,'RATED')
    updated=populated.execute_query('SELECT * FROM activities',fetch_one=True)
    assert updated['id']==a['id'] and updated['review_content']=='Edited synthetic review'


def test_review_without_rating_has_projection(populated):
    review_service.create_review(1,ReviewCreate(anime_id=1,content='A review without rating'))
    a=populated.execute_query('SELECT * FROM activities',fetch_one=True)
    assert a and a['review_content']=='A review without rating' and a['rating'] is None
