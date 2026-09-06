import asyncio
from pathlib import Path
import pytest


def test_startup_does_not_create_or_modify_database(db):
    from main import startup_event
    import inspect
    # Do not exercise legacy destructive startup even against a fixture: some
    # legacy scripts ignore DATABASE_PATH. This guard is supplementary only.
    assert 'verify_existing_users' not in inspect.getsource(startup_event)
    asyncio.run(startup_event())
    assert not Path(db.db_path).exists()


def test_release_init_rerun_and_readiness(db):
    import migrations
    assert migrations.is_ready(db.db_path) is False
    migrations.migrate(db.db_path, initialize=True)
    assert migrations.is_ready(db.db_path)
    with db.get_connection() as conn:
        before = list(conn.iterdump())
    migrations.migrate(db.db_path)
    with db.get_connection() as conn:
        assert list(conn.iterdump()) == before


def test_release_failure_rolls_back(db):
    import migrations
    def fail(conn):
        conn.execute('CREATE TABLE should_rollback(id INTEGER)')
        raise RuntimeError('intentional failure')
    with pytest.raises(RuntimeError, match='intentional'):
        migrations.migrate(db.db_path, initialize=True, extra_migrations=[(999, 'failure', fail)])
    with db.get_connection() as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []


def test_nested_helpers_share_transaction(db):
    db.execute_update('CREATE TABLE example(id INTEGER)')
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute_insert('INSERT INTO example VALUES (1)')
            raise RuntimeError('rollback')
    assert db.execute_query('SELECT * FROM example') == []
