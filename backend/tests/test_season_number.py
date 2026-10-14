import sqlite3


def test_season_number_ignores_ova_prequels_and_follows_tv_chain(populated):
    from services.anime_service import SEASON_NUMBER_SQL
    conn = sqlite3.connect(populated.db_path)
    rows = [(9001, 'TV'), (9002, 'OVA'), (9003, 'TV'), (9004, 'TV'), (9005, 'MOVIE')]
    conn.executemany("INSERT INTO anime(id, title_romaji, format) VALUES (?, ?, ?)", [(i, f't{i}', f) for i, f in rows])
    conn.executemany("INSERT INTO anime_relation(anime_id, related_anime_id, relation_type) VALUES (?, ?, 'PREQUEL')", [
        (9001, 9002),   # S1 has an OVA prequel -> still season 1
        (9003, 9001),   # S2
        (9004, 9003),   # S3 (chain, not direct edge count)
        (9004, 9005),   # movie prequel ignored
    ])
    conn.commit()
    got = dict(conn.execute(f"SELECT a.id, {SEASON_NUMBER_SQL} FROM anime a WHERE a.id BETWEEN 9001 AND 9004").fetchall())
    conn.close()
    assert got == {9001: 1, 9002: 1, 9003: 2, 9004: 3}
