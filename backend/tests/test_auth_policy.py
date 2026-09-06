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


def test_google_never_auto_links_existing_email(populated):
    info={'oauth_id':'synthetic-oauth','email':'demo1@example.com','name':'Demo','picture':'','email_verified':True}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(google_oauth_service.google_login_or_register(info))
    assert exc.value.status_code==409
    assert populated.execute_query('SELECT oauth_id,is_verified FROM users WHERE id=1',fetch_one=True)[:]==(None,0)


def test_oauth_account_and_stats_creation_rollback(populated):
    populated.execute_update("CREATE TRIGGER fail_stats BEFORE INSERT ON user_stats BEGIN SELECT RAISE(ABORT,'stats fail'); END")
    info={'oauth_id':'new-oauth','email':'new@example.com','name':'Demo','picture':'','email_verified':True}
    with pytest.raises(Exception,match='stats fail'):
        asyncio.run(google_oauth_service.google_login_or_register(info))
    assert populated.execute_query("SELECT * FROM users WHERE email='new@example.com'")==[]
