from pathlib import Path

from app.db.sqlite import get_connection


def run_sql_file(sql_file: str) -> None:
    sql_path = Path(sql_file)
    conn = get_connection()
    try:
        conn.executescript(sql_path.read_text())
        conn.commit()
    finally:
        conn.close()
