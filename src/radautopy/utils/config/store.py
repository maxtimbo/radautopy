import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS configs (
    filename TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    job_name TEXT GENERATED ALWAYS AS (json_extract(data, '$.job.job_name')) VIRTUAL,
    job_type TEXT GENERATED ALWAYS AS (json_extract(data, '$.job.job_type')) VIRTUAL,
    cron_expression TEXT GENERATED ALWAYS AS (json_extract(data, '$.job.cron_expression')) VIRTUAL,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def _connect(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get(filename: str, db_path: Path = DB_PATH) -> dict:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT data FROM configs WHERE filename = ?", (filename,)).fetchone()
    if row is None:
        raise FileNotFoundError(filename)
    return json.loads(row[0])


def exists(filename: str, db_path: Path = DB_PATH) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM configs WHERE filename = ?", (filename,)).fetchone()
    return row is not None


def save(filename: str, data: dict, db_path: Path = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO configs (filename, data, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(filename) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
            (filename, json.dumps(data), datetime.now(timezone.utc).isoformat()),
        )


def delete(filename: str, db_path: Path = DB_PATH) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute("DELETE FROM configs WHERE filename = ?", (filename,))
    return cur.rowcount > 0


def list_names(db_path: Path = DB_PATH) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT filename FROM configs ORDER BY filename").fetchall()
    return [r[0] for r in rows]


def list_jobs(db_path: Path = DB_PATH) -> dict[str, dict]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT filename, data FROM configs WHERE filename != 'email.json'").fetchall()
    return {filename: json.loads(data) for filename, data in rows}
