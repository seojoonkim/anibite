import pytest
from migrations import migrate
from models.rating import RatingCreate
from services.rating_service import create_or_update_rating


def test_legacy_trigger_replaced_without_losing_activity(populated):
    db=populated
    create_or_update_rating(1,RatingCreate(anime_id=1,rating=4,status='RATED'))
    aid=db.execute_query('SELECT id FROM activities',fetch_one=True)[0]
    db.execute_update("""CREATE TRIGGER legacy_bad_rating AFTER UPDATE ON user_ratings BEGIN
      INSERT OR REPLACE INTO activities(activity_type,user_id,item_id,username,rating,otaku_score)
      SELECT 'anime_rating',NEW.user_id,NEW.anime_id,u.username,NEW.rating,us.otaku_score
      FROM users u LEFT JOIN user_stats us ON u.id=NEW.user_id WHERE u.id=NEW.user_id;
    END""")
    db.execute_update('DELETE FROM schema_migrations')
    migrate(db.db_path)
    create_or_update_rating(1,RatingCreate(anime_id=1,rating=4.5,status='RATED'))
    rows=db.execute_query('SELECT id,rating FROM activities')
    assert len(rows)==1 and rows[0][0]==aid and rows[0][1]==4.5
    assert db.execute_query("SELECT sql FROM retired_triggers WHERE name='legacy_bad_rating'",fetch_one=True)


def test_legacy_post_triggers_retired(populated):
    from services.user_post_service import create_post, update_post, delete_post
    db = populated
    post = create_post(1, 'Synthetic post content')
    aid = db.execute_query('SELECT id FROM activities', fetch_one=True)[0]
    db.execute_update("""CREATE TRIGGER legacy_bad_post AFTER UPDATE ON user_posts BEGIN
      INSERT OR REPLACE INTO activities(activity_type,user_id,item_id,username,review_content)
      VALUES ('user_post',NEW.user_id,NEW.id,'demo1',NEW.content);
    END""")
    db.execute_update('DELETE FROM schema_migrations')
    migrate(db.db_path)
    update_post(post['id'], 1, 'Updated post content')
    assert db.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid
    delete_post(post['id'], 1)
    assert db.execute_query('SELECT id FROM activities', fetch_one=True)[0] == aid
    assert db.execute_query("SELECT sql FROM retired_triggers WHERE name='legacy_bad_post'", fetch_one=True)


def test_duplicate_legacy_data_aborts_without_deleting(db):
    db.execute_update('CREATE TABLE activities(id INTEGER PRIMARY KEY,activity_type TEXT,user_id INTEGER,item_id INTEGER)')
    db.execute_update("INSERT INTO activities VALUES (1,'anime_rating',1,1),(2,'anime_rating',1,1)")
    with pytest.raises(RuntimeError,match='duplicate'):
        migrate(db.db_path)
    assert db.execute_query('SELECT COUNT(*) FROM activities',fetch_one=True)[0]==2
