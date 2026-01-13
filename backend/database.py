"""
Database connection and utilities
SQLite3 connection management
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, List, Any
from config import DATABASE_PATH


class Database:
    """데이터베이스 연결 관리 클래스"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DATABASE_PATH)

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row  # Row 객체로 결과 반환
        # WAL 모드 활성화 (동시 읽기/쓰기 지원)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")  # 60초 대기
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(
        self, query: str, params: tuple = None, fetch_one: bool = False
    ) -> Optional[Any]:
        """쿼리 실행 헬퍼"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """INSERT 쿼리 실행 후 lastrowid 반환"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = None) -> int:
        """UPDATE/DELETE 쿼리 실행 후 영향받은 행 수 반환"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount


# Global database instance
db = Database()


def get_db() -> Database:
    """FastAPI dependency로 사용할 DB 인스턴스"""
    return db


def dict_from_row(row: sqlite3.Row) -> Dict:
    """sqlite3.Row를 dict로 변환"""
    if row is None:
        return None
    return dict(zip(row.keys(), row))


def dicts_from_rows(rows: List[sqlite3.Row]) -> List[Dict]:
    """sqlite3.Row 리스트를 dict 리스트로 변환"""
    if not rows:
        return []
    return [dict_from_row(row) for row in rows]
