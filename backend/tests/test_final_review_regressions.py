"""Bounded BF1/BF2 regressions using disposable synthetic databases only."""
import json
import sqlite3

import pytest


def test_following_feed_nonempty_follow_and_rank_column_alignment(populated):
    from services.feed_service import get_following_feed

    populated.execute_insert(
        'INSERT INTO user_follows(follower_id,following_id) VALUES (1,2)'
    )
    # A follow with no content must still compile every UNION branch.
    assert get_following_feed(1) == []
    metadata = {'rank': 'synthetic'}
    activity_id = populated.execute_insert(
        """INSERT INTO activities(
            activity_type,user_id,username,item_id,item_title,item_title_korean,
            item_title_native,item_image,rating,activity_time,anime_title,
            anime_title_korean,anime_title_native,anime_id,review_content,metadata
        ) VALUES ('rank_promotion',2,'demo2',17,'title','korean','native','/rank.svg',4,
                  '2026-01-01','anime','anime-ko','anime-native',1,'review',?)""",
        (json.dumps(metadata),),
    )
    rows = get_following_feed(1)
    assert len(rows) == 1
    row = rows[0]
    assert row['id'] == activity_id
    assert row['activity_type'] == 'rank_promotion'
    assert row['user_id'] == 2
    assert row['item_title_native'] == 'native'
    assert row['item_image'] == '/rank.svg'
    assert row['rating'] == 4
    assert row['status'] is None
    assert row['activity_time'] == '2026-01-01'
    assert row['anime_title_native'] == 'anime-native'
    assert row['anime_id'] == 1
    assert row['review_id'] is None
    assert row['review_content'] == 'review'
    assert row['post_content'] is None
    assert row['metadata'] == metadata
    assert get_following_feed(1, limit=1, offset=1) == []
    assert get_following_feed(2) == []


def legacy_likes(path, duplicate=False):
    with sqlite3.connect(path) as conn:
        conn.execute('''CREATE TABLE activity_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            activity_type TEXT, activity_user_id INTEGER, item_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('INSERT INTO activity_likes(id,activity_id,user_id) VALUES (7,1,2)')
        if duplicate:
            conn.execute('INSERT INTO activity_likes(id,activity_id,user_id) VALUES (8,1,2)')


def test_legacy_like_migration_establishes_conflict_target(tmp_path):
    from migrations import migrate, is_ready

    path = tmp_path / 'legacy.sqlite'
    legacy_likes(path)
    migrate(path)
    migrate(path)  # Release retries are idempotent.
    assert is_ready(path)
    with sqlite3.connect(path) as conn:
        for _ in range(2):
            conn.execute('''INSERT INTO activity_likes(activity_id,user_id)
                            VALUES (1,2) ON CONFLICT(activity_id,user_id) DO NOTHING''')
        assert conn.execute('SELECT id,activity_id,user_id FROM activity_likes').fetchall() == [(7,1,2)]
        conn.execute('''INSERT INTO activity_likes(activity_id,user_id)
                        VALUES (1,3) ON CONFLICT(activity_id,user_id) DO NOTHING''')
        assert conn.execute('SELECT COUNT(*) FROM activity_likes').fetchone()[0] == 2
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('INSERT INTO activity_likes(activity_id,user_id) VALUES (1,2)')


def test_legacy_like_duplicates_fail_closed_without_changes(tmp_path):
    from migrations import migrate, is_ready

    path = tmp_path / 'duplicate.sqlite'
    legacy_likes(path, duplicate=True)
    with sqlite3.connect(path) as conn:
        before = list(conn.iterdump())
    with pytest.raises(RuntimeError, match='activity_likes: duplicate identities require reviewed reference mapping'):
        migrate(path)
    with sqlite3.connect(path) as conn:
        assert list(conn.iterdump()) == before
    assert not is_ready(path)
