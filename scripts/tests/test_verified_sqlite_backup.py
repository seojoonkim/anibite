"""Exercise backup tooling only against newly created synthetic temporary DBs."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'verified_sqlite_backup.py'


class VerifiedBackupTests(unittest.TestCase):
    def test_snapshot_is_valid_private_and_includes_committed_wal_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.db', Path(tmp) / 'snapshot.db'
            with sqlite3.connect(source) as writer:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)')
                writer.execute("INSERT INTO sample(value) VALUES ('synthetic fixture')")
                writer.commit()
                result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(destination)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = json.loads(result.stdout)
                self.assertEqual(manifest['integrity_check'], 'ok')
                self.assertEqual(len(manifest['sha256']), 64)
                with sqlite3.connect(destination) as restored:
                    self.assertEqual(restored.execute('SELECT value FROM sample').fetchone()[0], 'synthetic fixture')
                self.assertEqual(destination.stat().st_mode & 0o777, 0o600)


    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'source.db', Path(tmp) / 'existing.db'
            with sqlite3.connect(source) as db:
                db.execute('CREATE TABLE fixture (id INTEGER)')
            destination.write_bytes(b'keep this file')
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(destination)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(destination.read_bytes(), b'keep this file')

    def test_missing_source_does_not_create_an_empty_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination = Path(tmp) / 'missing.db', Path(tmp) / 'snapshot.db'
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(destination)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(source.exists())
            self.assertFalse(destination.exists())

    def test_workflow_cannot_publish_raw_user_database_as_release(self):
        workflow = SCRIPT.parents[1] / '.github' / 'workflows' / 'backup-db.yml'
        content = workflow.read_text()
        self.assertNotIn('softprops/action-gh-release', content)
        self.assertNotIn('RAILWAY_TOKEN', content)
        self.assertNotIn('schedule:', content)


if __name__ == '__main__':
    unittest.main()
