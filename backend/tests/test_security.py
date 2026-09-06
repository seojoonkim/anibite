import asyncio
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


def test_token_without_expiry_rejected():
    import jwt
    from config import SECRET_KEY
    from utils.security import decode_access_token
    token=jwt.encode({'sub':'demo1'},SECRET_KEY,algorithm='HS256')
    assert decode_access_token(token) is None


def test_production_rejects_missing_secret():
    env = dict(os.environ, APP_ENV='production', PYTHONPATH='backend')
    env.pop('SECRET_KEY', None)
    result = subprocess.run([sys.executable, '-c', 'import config'], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'SECRET_KEY' in result.stderr


def test_admin_name_is_not_authority():
    from api.admin_editor import require_simon
    with pytest.raises(HTTPException) as exc:
        require_simon(SimpleNamespace(id=99, username='simon'))
    assert exc.value.status_code == 403


def test_oauth_only_password_fails_gracefully():
    from utils.security import verify_password
    assert verify_password('not-a-password', None) is False


def test_unverified_google_email_rejected(monkeypatch):
    from services import google_oauth_service as oauth
    monkeypatch.setattr(oauth.id_token, 'verify_oauth2_token', lambda *a: {
        'iss':'accounts.google.com', 'sub':'fixture-google-id',
        'email':'demo@example.com', 'email_verified': False})
    with pytest.raises(HTTPException) as exc:
        asyncio.run(oauth.verify_google_token('external-boundary-fixture'))
    assert exc.value.status_code == 401


def test_temporary_routes_not_registered():
    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    for method,path in [('post','/api/admin/verify-all-users'),('get','/api/admin/users-status'),('post','/api/admin-fix/fix-triggers'),('get','/api/debug/promotions')]:
        assert getattr(client,method)(path).status_code==404
    assert client.get('/api/admin/editor/search?q=demo').status_code in (401,403)
