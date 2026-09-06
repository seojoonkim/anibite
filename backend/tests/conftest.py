import os
import tempfile
from pathlib import Path

# Set before importing ANY application module; never load local credentials/data.
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'isolated-test-secret-not-for-deployment-123456789'
_sandbox = tempfile.TemporaryDirectory(prefix='anibite-pytest-')
os.environ['DATABASE_PATH'] = str(Path(_sandbox.name) / 'test.sqlite')
os.environ['ADMIN_USER_IDS'] = ''
for key in list(os.environ):
    if key.startswith(('R2_', 'SMTP_', 'GOOGLE_')):
        os.environ.pop(key)

import pytest
from database import Database

@pytest.fixture
def db(tmp_path, monkeypatch):
    import database
    database.db.db_path = str(tmp_path / 'fixture.sqlite')
    return database.db


@pytest.fixture
def populated(db):
    from migrations import migrate
    migrate(db.db_path, initialize=True)
    with db.transaction():
        for user_id in (1, 2):
            db.execute_insert("INSERT INTO users(id,username,email,display_name,is_verified,avatar_url) VALUES (?,?,?,?,0,'/demo.svg')", (user_id, f'demo{user_id}',f'demo{user_id}@example.com',f'Demo {user_id}'))
            db.execute_insert('INSERT INTO user_stats(user_id,otaku_score) VALUES (?,?)',(user_id,user_id*10))
        db.execute_insert("INSERT INTO anime(id,title_romaji,title_korean,episodes,duration) VALUES (1,'Synthetic Anime','합성 작품',12,24)")
        db.execute_insert("INSERT INTO character(id,name_full,name_korean) VALUES (1,'Synthetic Character','합성 캐릭터')")
        db.execute_insert("INSERT INTO anime_character VALUES (1,1,'MAIN')")
    return db
