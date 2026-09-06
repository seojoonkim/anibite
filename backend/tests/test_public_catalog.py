import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from models.rating import RatingCreate


@pytest.mark.parametrize('rating', [None, 0, 5.5, 3.2])
def test_rated_requires_valid_nonnull_half_step(rating):
    with pytest.raises(ValidationError):
        RatingCreate(anime_id=1, rating=rating, status='RATED')


def test_rated_missing_rating_rejected():
    with pytest.raises(ValidationError):
        RatingCreate(anime_id=1)


def test_character_detail_public_but_writes_protected(populated):
    from main import app
    from services.character_service import create_or_update_character_rating
    from utils.security import create_access_token
    create_or_update_character_rating(1, 1, 4, 'RATED')
    client = TestClient(app)
    response = client.get('/api/characters/1')
    assert response.status_code == 200
    assert response.json()['my_rating'] is None
    assert client.get('/api/characters/999').status_code == 404
    headers = {'Authorization': 'Bearer '+create_access_token({'sub': 'demo1'})}
    response = client.get('/api/characters/1', headers=headers)
    assert response.status_code == 200
    assert response.json()['my_rating'] == 4
    assert client.post('/api/characters/rate', json={'character_id': 1, 'rating': 5}).status_code in (401, 403)
    assert client.delete('/api/characters/rating/1').status_code in (401, 403)
