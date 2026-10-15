"""Guard: SQLite DB files contain user emails and password hashes and must never be tracked."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATTERN = re.compile(r'\.(db|sqlite|sqlite3|db-wal|db-shm)$', re.IGNORECASE)


def tracked_db_files():
    out = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if DB_PATTERN.search(p)]


class NoTrackedDatabaseTest(unittest.TestCase):
    def test_no_sqlite_files_tracked(self):
        self.assertEqual(tracked_db_files(), [], 'DB files must not be committed (user PII). Remove with git rm --cached.')


if __name__ == '__main__':
    unittest.main()
