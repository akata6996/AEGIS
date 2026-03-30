import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings


def _ensure_db_dir() -> None:
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON;')
    return conn


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
