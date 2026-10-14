"""
Catalog auto-sync from AniList.

Keeps the public anime catalog fresh without touching any user data:
- refreshes mutable fields (status, episodes, scores, popularity, dates, banner)
  for titles that are airing or about to air,
- adds newly popular titles from the current and next season,
- fills a missing Korean title from AniList Hangul synonyms.

Only catalog tables (anime, genre, anime_genre, catalog_sync_runs) are written.
Run manually:  python -m services.catalog_sync
In production the API process runs it on a timer (see start_scheduler);
disable with CATALOG_SYNC_ENABLED=0.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional

import requests

from database import db

logger = logging.getLogger(__name__)

ANILIST_URL = "https://graphql.anilist.co"
HANGUL = re.compile(r"[\uac00-\ud7a3]")
SEASONS = ["WINTER", "SPRING", "SUMMER", "FALL"]

MEDIA_FIELDS = """
  id idMal format status season seasonYear episodes duration source isAdult
  countryOfOrigin averageScore meanScore popularity favourites trending updatedAt
  siteUrl synonyms genres description(asHtml: false)
  title { romaji english native }
  startDate { year month day } endDate { year month day }
  coverImage { extraLarge large color } bannerImage
"""

PAGE_QUERY = """
query ($page: Int, $season: MediaSeason, $year: Int, $status: MediaStatus, $ids: [Int]) {
  Page(page: $page, perPage: 50) {
    pageInfo { hasNextPage }
    media(type: ANIME, season: $season, seasonYear: $year, status: $status,
          id_in: $ids, isAdult: false, sort: POPULARITY_DESC) { %s }
  }
}
""" % MEDIA_FIELDS

Fetcher = Callable[[Dict], Dict]


def _post(variables: Dict) -> Dict:
    for attempt in range(4):
        resp = requests.post(ANILIST_URL, json={"query": PAGE_QUERY, "variables": variables}, timeout=20)
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", "60")) + 1)
            continue
        resp.raise_for_status()
        time.sleep(0.8)  # stay well under AniList's 90 req/min
        return resp.json()["data"]["Page"]
    raise RuntimeError("AniList rate limit not cleared")


def _date(d: Optional[Dict]) -> Optional[str]:
    if not d or not d.get("year"):
        return None
    return f"{d['year']:04d}-{(d.get('month') or 1):02d}-{(d.get('day') or 1):02d}"


def current_and_next_season(now: Optional[datetime] = None):
    now = now or datetime.now(timezone.utc)
    idx = (now.month - 1) // 3
    cur = (SEASONS[idx], now.year)
    nxt = (SEASONS[(idx + 1) % 4], now.year + (1 if idx == 3 else 0))
    return [cur, nxt]


def _korean_title(media: Dict) -> Optional[str]:
    for name in media.get("synonyms") or []:
        if name and HANGUL.search(name):
            return name.strip()
    return None


def _ensure_tables():
    db.execute_update(
        """CREATE TABLE IF NOT EXISTS catalog_sync_runs(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             started_at TEXT DEFAULT CURRENT_TIMESTAMP,
             finished_at TEXT, updated INTEGER DEFAULT 0, inserted INTEGER DEFAULT 0,
             korean_filled INTEGER DEFAULT 0, error TEXT)"""
    )


def upsert_media(media: Dict, allow_insert: bool) -> str:
    """Return 'updated', 'inserted' or 'skipped'."""
    if media.get("isAdult"):
        return "skipped"
    cover = media.get("coverImage") or {}
    title = media.get("title") or {}
    fields = {
        "status": media.get("status"),
        "episodes": media.get("episodes"),
        "duration": media.get("duration"),
        "average_score": media.get("averageScore"),
        "mean_score": media.get("meanScore"),
        "popularity": media.get("popularity"),
        "favourites": media.get("favourites"),
        "trending": media.get("trending"),
        "start_date": _date(media.get("startDate")),
        "end_date": _date(media.get("endDate")),
        "banner_image_url": media.get("bannerImage"),
        "updated_at": media.get("updatedAt"),
    }
    existing = db.execute_query("SELECT id, title_korean FROM anime WHERE id = ?", (media["id"],), fetch_one=True)
    korean = _korean_title(media)
    if existing:
        sets = ", ".join(f"{k} = COALESCE(?, {k})" for k in fields)
        params = list(fields.values())
        if korean and not existing["title_korean"]:
            sets += ", title_korean = ?"
            params.append(korean)
        db.execute_update(f"UPDATE anime SET {sets}, crawled_at = CURRENT_TIMESTAMP WHERE id = ?", (*params, media["id"]))
        return "updated"
    if not allow_insert:
        return "skipped"
    row = {
        **fields,
        "id": media["id"],
        "id_mal": media.get("idMal"),
        "title_romaji": title.get("romaji"),
        "title_english": title.get("english"),
        "title_native": title.get("native"),
        "title_korean": korean,
        "type": "ANIME",
        "format": media.get("format"),
        "description": media.get("description"),
        "season": media.get("season"),
        "season_year": media.get("seasonYear"),
        "cover_image_url": cover.get("extraLarge") or cover.get("large"),
        "cover_image_color": cover.get("color"),
        "source": media.get("source"),
        "country_of_origin": media.get("countryOfOrigin"),
        "is_adult": 0,
        "site_url": media.get("siteUrl"),
    }
    cols = ", ".join(row)
    db.execute_insert(f"INSERT INTO anime ({cols}) VALUES ({', '.join('?' * len(row))})", tuple(row.values()))
    for genre in media.get("genres") or []:
        db.execute_insert("INSERT OR IGNORE INTO genre(name) VALUES (?)", (genre,))
        db.execute_insert(
            "INSERT OR IGNORE INTO anime_genre(anime_id, genre_id) SELECT ?, id FROM genre WHERE name = ?",
            (media["id"], genre),
        )
    return "inserted"


def _pages(fetch: Fetcher, variables: Dict, max_pages: int) -> Iterable[Dict]:
    for page in range(1, max_pages + 1):
        data = fetch({**variables, "page": page})
        yield from data.get("media") or []
        if not (data.get("pageInfo") or {}).get("hasNextPage"):
            break


def run_sync(fetch: Fetcher = _post, now: Optional[datetime] = None,
             new_per_season: int = 100, min_popularity: int = 5000) -> Dict[str, int]:
    """One sync pass. Never raises for a single bad record."""
    _ensure_tables()
    run_id = db.execute_insert("INSERT INTO catalog_sync_runs DEFAULT VALUES")
    counts = {"updated": 0, "inserted": 0, "korean_filled": 0}
    error = None
    try:
        seen = set()
        # 1) new/popular titles of the current and next season
        for season, year in current_and_next_season(now):
            for i, media in enumerate(_pages(fetch, {"season": season, "year": year}, max_pages=4)):
                if media["id"] in seen:
                    continue
                seen.add(media["id"])
                allow = i < new_per_season and (media.get("popularity") or 0) >= min_popularity
                had_korean = _has_korean(media["id"])
                result = upsert_media(media, allow_insert=allow)
                counts[result] = counts.get(result, 0) + (result != "skipped")
                if result != "skipped" and not had_korean and _has_korean(media["id"]):
                    counts["korean_filled"] += 1
        # 2) refresh every catalog title still airing / announced
        stale = [r["id"] for r in db.execute_query(
            "SELECT id FROM anime WHERE status IN ('RELEASING','NOT_YET_RELEASED','HIATUS')"
        ) if r["id"] not in seen]
        for start in range(0, len(stale), 50):
            for media in _pages(fetch, {"ids": stale[start:start + 50]}, max_pages=1):
                had_korean = _has_korean(media["id"])
                if upsert_media(media, allow_insert=False) == "updated":
                    counts["updated"] += 1
                    if not had_korean and _has_korean(media["id"]):
                        counts["korean_filled"] += 1
    except Exception as exc:  # keep the API healthy; record the failure
        error = f"{type(exc).__name__}: {exc}"[:500]
        logger.exception("catalog sync failed")
    db.execute_update(
        "UPDATE catalog_sync_runs SET finished_at=CURRENT_TIMESTAMP, updated=?, inserted=?, korean_filled=?, error=? WHERE id=?",
        (counts["updated"], counts["inserted"], counts["korean_filled"], error, run_id),
    )
    counts["error"] = error
    return counts


def _has_korean(anime_id: int) -> bool:
    row = db.execute_query("SELECT title_korean FROM anime WHERE id=?", (anime_id,), fetch_one=True)
    return bool(row and row["title_korean"])


def last_run() -> Optional[Dict]:
    try:
        row = db.execute_query("SELECT * FROM catalog_sync_runs ORDER BY id DESC LIMIT 1", fetch_one=True)
    except Exception:
        return None
    return dict(row) if row else None


_started = False


def start_scheduler() -> bool:
    """Start the daily background sync in production. Idempotent."""
    global _started
    from config import APP_ENV
    if _started or APP_ENV != "production" or os.getenv("CATALOG_SYNC_ENABLED", "1") == "0":
        return False
    interval = max(3600, int(os.getenv("CATALOG_SYNC_INTERVAL_SECONDS", str(24 * 3600))))
    first_delay = int(os.getenv("CATALOG_SYNC_FIRST_DELAY_SECONDS", "600"))

    def loop():
        time.sleep(first_delay)
        while True:
            try:
                prev = last_run()
                due = True
                if prev and prev.get("finished_at") and not prev.get("error"):
                    finished = datetime.fromisoformat(prev["finished_at"]).replace(tzinfo=timezone.utc)
                    due = (datetime.now(timezone.utc) - finished).total_seconds() >= interval - 60
                if due:
                    logger.info("catalog sync result: %s", run_sync())
            except Exception:
                logger.exception("catalog sync loop error")
            time.sleep(min(interval, 3600))

    threading.Thread(target=loop, name="catalog-sync", daemon=True).start()
    _started = True
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_sync())
