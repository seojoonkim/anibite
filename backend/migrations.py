"""Explicit, transactional SQLite release migrations. Never imported for writes."""
import argparse
import hashlib
import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).parent / 'schema'
VERSION = 1


def statements(script):
    pending = ''
    for line in script.splitlines(True):
        pending += line
        if sqlite3.complete_statement(pending):
            yield pending
            pending = ''
    if pending.strip() and not all(x.strip().startswith('--') or not x.strip() for x in pending.splitlines()):
        raise ValueError('Incomplete migration SQL')


def execute_script(conn, script):
    # executescript() commits implicitly; individual statements retain the lock.
    for sql in statements(script):
        conn.execute(sql)


def add_columns(conn, table, definitions):
    columns = {row[1] for row in conn.execute(f'PRAGMA table_info({table})')}
    for name, definition in definitions.items():
        if name not in columns:
            conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')


def baseline(conn):
    # Refuse ambiguous legacy identities instead of deleting or remapping blindly.
    unique_keys = [('activities','activity_type,user_id,item_id'),
                   ('user_ratings','user_id,anime_id'), ('character_ratings','user_id,character_id'),
                   ('user_reviews','user_id,anime_id'), ('character_reviews','user_id,character_id'),
                   ('activity_likes','activity_id,user_id')]
    for table, keys in unique_keys:
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name=? AND type='table'", (table,)).fetchone():
            if conn.execute(f'SELECT 1 FROM {table} GROUP BY {keys} HAVING COUNT(*)>1 LIMIT 1').fetchone():
                raise RuntimeError(f'{table}: duplicate identities require reviewed reference mapping')
    conn.execute('CREATE TABLE IF NOT EXISTS retired_triggers(name TEXT PRIMARY KEY, sql TEXT NOT NULL, retired_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    for name, table, sql in conn.execute("SELECT name,tbl_name,sql FROM sqlite_master WHERE type='trigger'").fetchall():
        if table in {'user_ratings','character_ratings','user_reviews','character_reviews','user_posts'} and 'activities' in sql.lower():
            conn.execute('INSERT OR IGNORE INTO retired_triggers(name,sql) VALUES (?,?)',(name,sql))
            conn.execute('DROP TRIGGER "' + name.replace('"','""') + '"')
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='anime' AND type='table'").fetchone():
        execute_script(conn, (SCHEMA / 'catalog.sql').read_text())
    execute_script(conn, (SCHEMA / 'users.sql').read_text())
    execute_script(conn, (SCHEMA / 'social.sql').read_text())
    add_columns(conn, 'review_comments', {'review_type':"TEXT DEFAULT 'anime'"})
    add_columns(conn, 'anime', {'title_korean':'TEXT', 'title_korean_official':'TEXT'})
    add_columns(conn, 'character', {'name_korean':'TEXT'})
    add_columns(conn, 'users', {'preferred_language':"TEXT DEFAULT 'ko'", 'oauth_provider':'TEXT', 'oauth_id':'TEXT',
                'is_verified':'INTEGER DEFAULT 0', 'verification_token':'TEXT', 'verification_token_expires':'TEXT'})
    add_columns(conn, 'user_stats', {'total_character_ratings':'INTEGER DEFAULT 0'})
    add_columns(conn, 'activities', {'item_year':'INTEGER','item_title_native':'TEXT','anime_title_native':'TEXT','metadata':'TEXT'})
    # CREATE TABLE IF NOT EXISTS cannot add constraints to legacy tables.
    for table, keys in unique_keys:
        conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS release_unique_{table} ON {table}({keys})')


def checksum():
    digest = hashlib.sha256(Path(__file__).read_bytes())
    for file in sorted(SCHEMA.glob('*.sql')):
        digest.update(file.read_bytes())
    return digest.hexdigest()


def migrate(path, initialize=False, extra_migrations=()):
    path = Path(path).resolve()
    if not initialize and not path.is_file():
        raise RuntimeError('Database missing; explicitly initialize a new database')
    if not path.parent.is_dir():
        raise RuntimeError('Database parent directory must exist')
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    try:
        conn.execute('BEGIN EXCLUSIVE')  # SQLite cross-process release lock
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if not tables and not initialize:
            raise RuntimeError('Empty database; explicit init required')
        conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)')
        for version, digest, apply in [(VERSION, checksum(), baseline), *extra_migrations]:
            row = conn.execute('SELECT checksum FROM schema_migrations WHERE version=?', (version,)).fetchone()
            if row:
                if row[0] != digest:
                    raise RuntimeError('Migration checksum mismatch; release review required')
                continue
            apply(conn)
            conn.execute('INSERT INTO schema_migrations(version,checksum) VALUES (?,?)', (version,digest))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_ready(path):
    try:
        with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=1) as conn:
            row = conn.execute('SELECT checksum FROM schema_migrations WHERE version=?',(VERSION,)).fetchone()
            if not row or row[0] != checksum():
                return False
            for table in ['users','anime','character','activities','user_ratings','character_ratings','activity_comments','activity_likes']:
                conn.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchall()
            return True
    except (sqlite3.Error, OSError):
        return False


def main():
    from config import DATABASE_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init','migrate','check'])
    args = parser.parse_args()
    if args.command == 'check':
        if not is_ready(DATABASE_PATH):
            raise SystemExit('Database/schema not ready; run approved release migration')
    else:
        migrate(DATABASE_PATH, initialize=args.command == 'init')
    print('Database schema ready')


if __name__ == '__main__':
    main()
