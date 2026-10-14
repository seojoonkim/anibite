from datetime import datetime, timezone
from services import catalog_sync


def media(i, **kw):
    base = {'id': i, 'idMal': None, 'format': 'TV', 'status': 'RELEASING', 'season': 'FALL', 'seasonYear': 2026,
            'episodes': 12, 'duration': 24, 'source': 'MANGA', 'isAdult': False, 'countryOfOrigin': 'JP',
            'averageScore': 80, 'meanScore': 80, 'popularity': 50000, 'favourites': 10, 'trending': 5,
            'updatedAt': 1, 'siteUrl': f'https://anilist.co/anime/{i}', 'synonyms': [], 'genres': ['Action'],
            'description': 'd', 'title': {'romaji': f'T{i}', 'english': None, 'native': None},
            'startDate': {'year': 2026, 'month': 10, 'day': 3}, 'endDate': {}, 'coverImage': {'extraLarge': f'https://img/{i}.jpg', 'color': '#fff'},
            'bannerImage': None}
    base.update(kw)
    return base


def test_sync_inserts_new_updates_existing_and_fills_korean(populated):
    populated.execute_update("UPDATE anime SET status='RELEASING', title_korean=NULL, episodes=1 WHERE id=1")
    calls = []

    def fake(vars):
        calls.append(vars)
        if vars.get('ids'):
            return {'media': [media(1, episodes=24, synonyms=['합성 작품 정식'])], 'pageInfo': {'hasNextPage': False}}
        if vars['season'] == 'FALL':
            return {'media': [media(500, synonyms=['새 작품']), media(501, popularity=10), media(502, isAdult=True)],
                    'pageInfo': {'hasNextPage': False}}
        return {'media': [], 'pageInfo': {'hasNextPage': False}}

    out = catalog_sync.run_sync(fetch=fake, now=datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert out['error'] is None
    assert out['inserted'] == 1 and out['updated'] == 1 and out['korean_filled'] == 2
    row = populated.execute_query('SELECT episodes,title_korean FROM anime WHERE id=1', fetch_one=True)
    assert tuple(row) == (24, '합성 작품 정식')
    assert populated.execute_query('SELECT title_korean FROM anime WHERE id=500', fetch_one=True)[0] == '새 작품'
    assert populated.execute_query('SELECT COUNT(*) FROM anime WHERE id IN (501,502)', fetch_one=True)[0] == 0
    assert populated.execute_query("SELECT COUNT(*) FROM anime_genre WHERE anime_id=500", fetch_one=True)[0] == 1
    # user tables untouched
    assert populated.execute_query('SELECT COUNT(*) FROM users', fetch_one=True)[0] == 2
    assert catalog_sync.last_run()['inserted'] == 1


def test_sync_records_failure_without_raising(populated):
    def boom(vars):
        raise RuntimeError('network down')
    out = catalog_sync.run_sync(fetch=boom)
    assert 'network down' in out['error']


def test_season_rollover():
    assert catalog_sync.current_and_next_season(datetime(2026, 11, 1, tzinfo=timezone.utc)) == [('FALL', 2026), ('WINTER', 2027)]


def test_scheduler_disabled_outside_production():
    assert catalog_sync.start_scheduler() is False
