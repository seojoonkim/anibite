from fastapi.testclient import TestClient
from utils.security import create_access_token
from services.activity_service import get_activities


def test_explicit_like_routes(populated):
    from main import app
    populated.execute_insert("INSERT INTO activities(id,activity_type,user_id,username) VALUES (1,'user_post',1,'demo1')")
    client=TestClient(app)
    headers={'Authorization':'Bearer '+create_access_token({'sub':'demo2'})}
    for _ in range(2):
        response=client.put('/api/activities/1/like',headers=headers)
        assert response.status_code==200 and response.json()['liked'] is True
    for _ in range(2):
        response=client.delete('/api/activities/1/like',headers=headers)
        assert response.status_code==200 and response.json()['liked'] is False


def test_feed_ties_stably_ordered_and_engagement_page_first(populated):
    for i in range(1,6):
        populated.execute_insert("INSERT INTO activities(id,activity_type,user_id,username,activity_time,review_content) VALUES (?,'user_post',1,'demo1','2026-01-01','Synthetic post')",(i,))
        populated.execute_insert('INSERT INTO activity_likes(activity_id,user_id) VALUES (?,2)',(i,))
    with populated.transaction() as conn:
        traced=[]
        conn.set_trace_callback(traced.append)
        result=get_activities(populated,limit=2,current_user_id=2)
    assert [a['id'] for a in result['items']]==[5,4]
    assert all(a['likes_count']==1 and a['user_liked'] for a in result['items'])
    engagement=[q.lower() for q in traced if 'group by activity_id' in q.lower()]
    assert engagement and all('page' in q or 'activity_id in' in q for q in engagement)


def test_image_download_routes_use_threadpool():
    import inspect
    from routers import image_proxy
    routes=[r for r in image_proxy.router.routes if hasattr(r,'endpoint')]
    assert routes and all(not inspect.iscoroutinefunction(r.endpoint) for r in routes)
