"""Retired unsafe downloader; compatibility entry point for old launch commands.

Never download or backfill a database during application startup. A missing or
unmigrated volume must fail closed until an operator restores/migrates it.
"""


def main():
    from config import DATABASE_PATH
    from migrations import is_ready
    if not is_ready(DATABASE_PATH):
        raise SystemExit('Database/schema not ready; restore an approved snapshot and run the release migration')
    print('Database schema ready; legacy automatic download is disabled')


if __name__ == '__main__':
    main()
