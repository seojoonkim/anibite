"""Release guards tested only against synthetic temporary databases."""
import ast
from pathlib import Path

import pytest


def test_legacy_downloader_has_no_import_time_network_or_db_writes():
    # Never execute the old downloader: it hard-codes the production volume.
    tree = ast.parse((Path(__file__).parents[1] / 'download_db.py').read_text())
    unsafe = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'":
            continue
        unsafe.append(ast.unparse(node))
    assert unsafe == [], 'Legacy downloader must not mutate/download on import'


def test_upgrade_installs_unique_keys_on_legacy_tables(db):
    from migrations import migrate, execute_script, SCHEMA
    with db.get_connection() as conn:
        execute_script(conn, (SCHEMA / 'catalog.sql').read_text())
        execute_script(conn, (SCHEMA / 'users.sql').read_text().replace('UNIQUE(user_id, anime_id)', 'CHECK(user_id > 0)'))
        execute_script(conn, (SCHEMA / 'social.sql').read_text().replace('UNIQUE(user_id, character_id)', 'CHECK(user_id > 0)').replace('UNIQUE(user_id,character_id)', 'CHECK(user_id > 0)').replace('UNIQUE(activity_type,user_id,item_id)', 'CHECK(user_id > 0)'))
    migrate(db.db_path)
    with db.get_connection() as conn:
        # Preparing UPSERT fails unless a matching uniqueness constraint exists.
        for table, key in [('user_ratings','anime_id'), ('character_ratings','character_id'), ('user_reviews','anime_id'), ('character_reviews','character_id')]:
            conn.execute(f'EXPLAIN INSERT INTO {table}(user_id,{key}) VALUES (1,1) ON CONFLICT(user_id,{key}) DO NOTHING')
        conn.execute("EXPLAIN INSERT INTO activities(activity_type,user_id,item_id,username) VALUES ('anime_rating',1,1,'demo') ON CONFLICT(activity_type,user_id,item_id) DO NOTHING")
