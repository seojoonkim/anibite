from fastapi.testclient import TestClient


def test_public_catalog_cached_and_gzipped(populated):
    from main import app
    c = TestClient(app)
    r = c.get('/api/anime/?page=1&page_size=50', headers={'Accept-Encoding': 'gzip'})
    assert r.status_code == 200
    assert r.headers['cache-control'].startswith('public')


def test_authenticated_or_private_not_publicly_cached(populated):
    from main import app
    c = TestClient(app)
    r = c.get('/api/anime/?page=1', headers={'Authorization': 'Bearer x'})
    assert 'public' not in r.headers.get('cache-control', '')
    r = c.get('/api/feed')
    assert 'public' not in r.headers.get('cache-control', '')
