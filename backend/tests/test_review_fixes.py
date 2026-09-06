import pytest
from services import review_service, character_review_service, projection_service
from models.review import ReviewCreate
from models.character_review import CharacterReviewCreate


@pytest.mark.parametrize('kind', ['anime', 'character'])
@pytest.mark.parametrize('with_review', [False, True])
def test_empty_projection_visibility(populated, kind, with_review):
    from services.activity_service import get_activities, get_activity_by_id
    from services.rating_service import create_or_update_rating
    from services.character_service import create_or_update_character_rating
    from models.rating import RatingCreate
    if with_review:
        make_review(kind)
    if kind == 'anime':
        create_or_update_rating(1, RatingCreate(anime_id=1, rating=4, status='RATED'))
        create_or_update_rating(1, RatingCreate(anime_id=1, status='PASS'))
    else:
        create_or_update_character_rating(1, 1, 4, 'RATED')
        create_or_update_character_rating(1, 1, None, 'NOT_INTERESTED')
    aid = populated.execute_query('SELECT id FROM activities', fetch_one=True)[0]
    for filters in [{}, {'user_id': 1}, {'activity_type': kind+'_rating', 'item_id': 1}]:
        result = get_activities(populated, **filters)
        assert result['total'] == int(with_review)
        assert len(result['items']) == int(with_review)
        assert get_activities(populated, offset=1, **filters)['items'] == []
    assert (get_activity_by_id(aid) is not None) == with_review
    from services.feed_service import get_global_feed, get_user_feed
    assert len(get_global_feed()) == int(with_review)
    assert len(get_user_feed(1)) == int(with_review)
    if kind == 'character':
        from services.profile_service import get_character_ratings
        assert all(row['rating'] is not None for row in get_character_ratings(1) if row['status'] == 'RATED')


def test_review_rating_reads_use_user_item_identity(populated):
    review = make_review('anime')
    assert review.user_rating == 4
    assert review_service.get_my_review(1, 1).user_rating == 4
    assert review_service.get_user_reviews(1).items[0].user_rating == 4
    # Legacy review rows without linkage must work too.
    populated.execute_update('UPDATE user_reviews SET rating_id=NULL')
    assert review_service.get_review_by_id(review.id).user_rating == 4
    from services.rating_service import delete_rating
    delete_rating(1, 1)
    assert review_service.get_review_by_id(review.id).user_rating is None


@pytest.mark.parametrize('operation', ['create', 'update', 'delete'])
@pytest.mark.parametrize('fail', [False, True])
def test_fresh_post_projection_lifecycle(populated, monkeypatch, operation, fail):
    from services import user_post_service as posts
    from services.activity_service import get_activities, get_activity_by_id
    import sqlite3
    post = None if operation == 'create' else posts.create_post(1, 'Original post content')
    # Abort the projection write at SQLite's boundary, not a mocked service.
    if fail:
        event = 'INSERT' if operation == 'create' else 'UPDATE'
        populated.execute_update(f"CREATE TRIGGER reject_projection BEFORE {event} ON activities BEGIN SELECT RAISE(ABORT, 'projection failure'); END")
    def perform():
        if operation == 'create':
            return posts.create_post(1, 'Original post content')
        if operation == 'update':
            return posts.update_post(post['id'], 1, 'Updated post content')
        return posts.delete_post(post['id'], 1)
    if fail:
        with pytest.raises(sqlite3.IntegrityError, match='projection failure'):
            perform()
        if operation == 'create':
            assert posts.get_user_posts(1) == []
        else:
            assert posts.get_post(post['id'])['content'] == 'Original post content'
            assert get_activities(populated)['items'][0]['review_content'] == 'Original post content'
    else:
        result = perform()
        if operation == 'create':
            post = result
        a = populated.execute_query('SELECT * FROM activities', fetch_one=True)
        assert a is not None and a['item_id'] == post['id']
        if operation == 'delete':
            assert posts.get_post(post['id']) is None
            assert a['review_content'] is None
            assert get_activity_by_id(a['id']) is None
        else:
            assert a['review_content'] == posts.get_post(post['id'])['content']
            assert get_activities(populated)['total'] == 1
            aid = a['id']
            assert not posts.update_post(post['id'], 2, 'Unauthorized update')
            assert not posts.delete_post(post['id'], 2)
            assert populated.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid


@pytest.mark.parametrize('kind', ['anime', 'character'])
def test_item_review_feed_retains_review_without_rating(populated, kind):
    from services.rating_service import delete_rating, create_or_update_rating
    from services.character_service import delete_character_rating, create_or_update_character_rating
    from models.rating import RatingCreate
    review = make_review(kind)
    if kind == 'anime':
        delete_rating(1, 1)
        result = review_service.get_anime_reviews(1)
    else:
        delete_character_rating(1, 1)
        result = character_review_service.get_character_reviews(1)
        assert character_review_service.get_my_character_review(1, 1).content == review.content
    assert result.total == 1 and len(result.items) == 1
    assert result.items[0].content == review.content and result.items[0].user_rating is None
    delete_review(kind, False, review.id)
    if kind == 'anime':
        create_or_update_rating(1, RatingCreate(anime_id=1, status='PASS'))
        result = review_service.get_anime_reviews(1)
    else:
        create_or_update_character_rating(1, 1, None, 'NOT_INTERESTED')
        result = character_review_service.get_character_reviews(1)
    assert result.total == 0 and result.items == []


@pytest.mark.parametrize('kind', ['anime', 'character', 'post'])
def test_activity_delete_deletes_sources_atomically(populated, kind):
    from services.activity_service import delete_activity, get_activity_by_id
    if kind == 'post':
        from services.user_post_service import create_post
        create_post(1, 'Synthetic post content')
        tables = ['user_posts']
    else:
        make_review(kind)
        tables = ['user_ratings', 'user_reviews'] if kind == 'anime' else ['character_ratings', 'character_reviews']
    aid = populated.execute_query('SELECT id FROM activities', fetch_one=True)[0]
    populated.execute_insert('INSERT INTO activity_bookmarks(user_id,activity_id) VALUES (2,?)', (aid,))
    assert not delete_activity(aid, 2)
    assert delete_activity(aid, 1)
    for table in tables:
        assert populated.execute_query(f'SELECT * FROM {table}') == []
    assert get_activity_by_id(aid) is None
    assert populated.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid
    assert populated.execute_query('SELECT activity_id FROM activity_bookmarks', fetch_one=True)[0] == aid


def make_review(kind):
    if kind == 'anime':
        return review_service.create_review(1, ReviewCreate(anime_id=1, rating=4, content='Synthetic review content'))
    return character_review_service.create_character_review(1, CharacterReviewCreate(character_id=1, rating=4, content='Synthetic review content'))


def delete_review(kind, by_item, review_id):
    if kind == 'anime':
        return review_service.delete_review_by_anime(1, 1) if by_item else review_service.delete_review(review_id, 1)
    return character_review_service.delete_character_review_by_character(1, 1) if by_item else character_review_service.delete_character_review(review_id, 1)


@pytest.mark.parametrize('kind', ['anime', 'character'])
@pytest.mark.parametrize('by_item', [False, True])
@pytest.mark.parametrize('fail', [False, True])
def test_review_delete_syncs_atomically(populated, monkeypatch, kind, by_item, fail):
    review = make_review(kind)
    before = dict(populated.execute_query('SELECT * FROM activities', fetch_one=True))
    if fail:
        def broken(*args):
            raise RuntimeError('projection failure')
        monkeypatch.setattr(projection_service, 'sync_projection', broken)
        with pytest.raises(RuntimeError, match='projection failure'):
            delete_review(kind, by_item, review.id)
        table = 'user_reviews' if kind == 'anime' else 'character_reviews'
        assert populated.execute_query(f'SELECT id FROM {table}', fetch_one=True)
        assert dict(populated.execute_query('SELECT * FROM activities', fetch_one=True)) == before
    else:
        assert delete_review(kind, by_item, review.id)
        after = populated.execute_query('SELECT * FROM activities', fetch_one=True)
        assert after['id'] == before['id']
        assert after['review_content'] is None and after['review_title'] is None
        assert after['rating'] == 4


@pytest.mark.parametrize('kind', ['anime', 'character'])
@pytest.mark.parametrize('fail', [False, True])
def test_rating_delete_preserves_review_identity(populated, monkeypatch, kind, fail):
    from services.rating_service import delete_rating
    from services.character_service import delete_character_rating
    make_review(kind)
    before = dict(populated.execute_query('SELECT * FROM activities', fetch_one=True))
    aid = before['id']
    for table, cols, vals in [
        ('activity_likes', 'activity_id,user_id', (aid, 2)),
        ('activity_bookmarks', 'activity_id,user_id', (aid, 2)),
        ('activity_comments', 'activity_id,user_id,content', (aid, 2, 'Keep comment')),
    ]:
        populated.execute_insert(f"INSERT INTO {table}({cols}) VALUES ({','.join('?' for _ in vals)})", vals)
    delete = delete_rating if kind == 'anime' else delete_character_rating
    if fail:
        def broken(*args):
            raise RuntimeError('projection failure')
        monkeypatch.setattr(projection_service, 'sync_projection', broken)
        with pytest.raises(RuntimeError, match='projection failure'):
            delete(1, 1)
        table = 'user_ratings' if kind == 'anime' else 'character_ratings'
        assert populated.execute_query(f'SELECT id FROM {table}', fetch_one=True)
        assert dict(populated.execute_query('SELECT * FROM activities', fetch_one=True)) == before
    else:
        assert delete(1, 1)
        after = populated.execute_query('SELECT * FROM activities', fetch_one=True)
        assert after is not None
        assert after['id'] == aid and after['rating'] is None
        assert after['review_content'] == before['review_content']
        make_review(kind)
        assert populated.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid
    for table in ['activity_likes', 'activity_bookmarks', 'activity_comments']:
        assert populated.execute_query(f'SELECT activity_id FROM {table}', fetch_one=True)[0] == aid
