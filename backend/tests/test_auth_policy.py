import asyncio
import pytest
from fastapi import HTTPException
from models.user import UserRegister,UserLogin
from services import auth_service,google_oauth_service
from utils.security import decode_access_token


def test_registration_token_matches_login_subject(populated):
    token=auth_service.register_user(UserRegister(username='newdemo',email='newdemo@example.com',password='Synthetic-Password-123'))
    assert decode_access_token(token.access_token)['sub']=='newdemo'
    assert populated.execute_query("SELECT is_verified FROM users WHERE username='newdemo'",fetch_one=True)[0]==0


def test_google_links_verified_email_and_kills_unverified_squatter_password(populated):
    # demo1 is an unverified local account; a pre-registered squatter must lose password access.
    populated.execute_update("UPDATE users SET password_hash='x' WHERE id=1")
    info={'oauth_id':'synthetic-oauth','email':'demo1@example.com','name':'Demo','picture':'','email_verified':True}
    token=asyncio.run(google_oauth_service.google_login_or_register(info))
    assert token.user.id==1
    row=populated.execute_query('SELECT oauth_provider,oauth_id,is_verified,password_hash FROM users WHERE id=1',fetch_one=True)
    assert tuple(row)==('google','synthetic-oauth',1,None)
    # second login with the same Google identity keeps working
    assert asyncio.run(google_oauth_service.google_login_or_register(info)).user.id==1


def test_google_link_keeps_password_of_verified_account(populated):
    populated.execute_update("UPDATE users SET password_hash='keep', is_verified=1 WHERE id=2")
    info={'oauth_id':'g-2','email':'demo2@example.com','name':'Demo','picture':'','email_verified':True}
    assert asyncio.run(google_oauth_service.google_login_or_register(info)).user.id==2
    assert populated.execute_query('SELECT password_hash FROM users WHERE id=2',fetch_one=True)[0]=='keep'


def test_google_never_rebinds_other_google_identity(populated):
    populated.execute_update("UPDATE users SET oauth_provider='google', oauth_id='original' WHERE id=1")
    info={'oauth_id':'attacker','email':'demo1@example.com','name':'Demo','picture':'','email_verified':True}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(google_oauth_service.google_login_or_register(info))
    assert exc.value.status_code==409
    assert populated.execute_query('SELECT oauth_id FROM users WHERE id=1',fetch_one=True)[0]=='original'


def test_oauth_account_and_stats_creation_rollback(populated):
    populated.execute_update("CREATE TRIGGER fail_stats BEFORE INSERT ON user_stats BEGIN SELECT RAISE(ABORT,'stats fail'); END")
    info={'oauth_id':'new-oauth','email':'new@example.com','name':'Demo','picture':'','email_verified':True}
    with pytest.raises(Exception,match='stats fail'):
        asyncio.run(google_oauth_service.google_login_or_register(info))
    assert populated.execute_query("SELECT * FROM users WHERE email='new@example.com'")==[]


def test_rating_page_stats_for_user_with_no_ratings(populated):
    from services import rating_page_service as rps
    a=rps.get_anime_for_rating_stats(1)
    assert a['rated']==0 and a['remaining']==a['total']
    c=rps.get_characters_for_rating_stats(1)
    assert c['rated']==0 and c['remaining']==0
    w=rps.get_review_writing_stats(1)
    assert w['total']=={'reviewed':0,'pending':0}


def test_character_reviews_are_public(populated):
    from fastapi.testclient import TestClient
    from main import app
    r=TestClient(app).get('/api/character-reviews/character/1')
    assert r.status_code==200, r.text
