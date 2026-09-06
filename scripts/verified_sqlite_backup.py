"""Create a private, verified SQLite snapshot; never upload or overwrite a DB.

Run explicitly on the host holding the database. Do not copy a live SQLite
main file with filesystem tools: committed rows may still live in its WAL.
This command does not schedule backups, encrypt files, or contact services.
"""
from contextlib import closing
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from urllib.parse import quote


def create_snapshot(source: Path, destination: Path, timeout: float = 30.0) -> dict:
    source = source.resolve(strict=True)
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Destination already exists; snapshots never overwrite files')
    started = time.monotonic()

    def check_deadline(_status, _remaining, _total):
        if time.monotonic() - started > timeout:
            raise TimeoutError('Snapshot timed out; no completed snapshot was published')

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.anibite-snapshot-', suffix='.db', dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
        with closing(sqlite3.connect(f'file:{quote(str(source))}?mode=ro', uri=True, timeout=timeout)) as origin:
            with closing(sqlite3.connect(temporary)) as snapshot:
                origin.backup(snapshot, pages=128, progress=check_deadline, sleep=0.01)
                result = snapshot.execute('PRAGMA integrity_check').fetchall()
                if result != [('ok',)]:
                    raise ValueError('Snapshot failed SQLite integrity_check')
        with temporary.open('rb') as handle:
            digest = hashlib.sha256()
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
            os.fsync(handle.fileno())
        # Atomic no-clobber publication on the same filesystem. A concurrent
        # writer creating destination causes failure rather than replacement.
        os.link(temporary, destination)
        return {'path': str(destination), 'bytes': destination.stat().st_size,
                'sha256': digest.hexdigest(), 'integrity_check': 'ok'}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--timeout', type=float, default=30.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    try:
        print(json.dumps(create_snapshot(args.source, args.destination, args.timeout)))
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f'Backup failed: {error}\n')


if __name__ == '__main__':
    main()
