import pytest
from services import activity_service as service

@pytest.fixture
def activities(populated):
    for i in (1,2):
        populated.execute_insert("INSERT INTO activities(id,activity_type,user_id,username,item_id,review_content) VALUES (?,'user_post',1,'demo1',?,'Synthetic post')",(i,i))
    return populated

@pytest.mark.parametrize('content',['','   ','x'*1001])
def test_comment_length_rejected(activities,content):
    with pytest.raises(ValueError):
        service.create_activity_comment(1,2,content)
    assert activities.execute_query('SELECT * FROM activity_comments')==[]


def test_comment_parent_must_belong_to_activity(activities):
    root=service.create_activity_comment(1,2,'root')
    with pytest.raises(ValueError):
        service.create_activity_comment(2,2,'cross activity',root['id'])


def test_comment_depth_is_bounded(activities):
    root=service.create_activity_comment(1,2,'root')
    reply=service.create_activity_comment(1,2,'reply',root['id'])
    with pytest.raises(ValueError):
        service.create_activity_comment(1,2,'too deep',reply['id'])


def test_explicit_likes_idempotent(activities):
    assert service.set_activity_like(1,2,True)
    assert service.set_activity_like(1,2,True)
    assert activities.execute_query('SELECT COUNT(*) FROM activity_likes',fetch_one=True)[0]==1
    assert activities.execute_query('SELECT COUNT(*) FROM notifications',fetch_one=True)[0]==1
    assert service.set_activity_like(1,2,False) is False
    assert service.set_activity_like(1,2,False) is False
    assert activities.execute_query('SELECT * FROM activity_likes')==[]


def test_comment_query_is_bounded(activities):
    with activities.transaction():
        for _ in range(125):
            activities.execute_insert("INSERT INTO activity_comments(activity_id,user_id,content) VALUES (1,2,'root')")
    comments=service.get_activity_comments(1,limit=20,offset=0)
    assert len(comments)==20
