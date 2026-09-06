import pytest
from fastapi.testclient import TestClient


def test_demo_seed_is_explicit_local_only_and_ordinary_login(db):
    from demo_seed import seed
    seed(db.db_path,'Synthetic-Demo-Password-123')
    from main import app
    client=TestClient(app)
    response=client.post('/api/auth/login',json={'username':'anibitedemo','password':'Synthetic-Demo-Password-123'})
    assert response.status_code==200
    token=response.json()['access_token']
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==200
    assert client.get('/api/anime/?page=1&page_size=20').status_code==200
    assert client.get('/api/anime/1').status_code==200
    assert client.get('/api/characters/1',headers={'Authorization':'Bearer '+token}).status_code==200
    assert client.get('/ready').status_code==200
    with pytest.raises(RuntimeError,match='existing'):
        seed(db.db_path,'Synthetic-Demo-Password-123')


def test_demo_seed_refuses_production(tmp_path,monkeypatch):
    from demo_seed import seed
    monkeypatch.setenv('APP_ENV','production')
    path=tmp_path/'production.sqlite'
    with pytest.raises(RuntimeError):
        seed(path,'Synthetic-Demo-Password-123')
    assert not path.exists()
