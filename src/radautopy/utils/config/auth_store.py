import hashlib
import hmac
import json
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import DB_PATH
from .store import _connect

ROLES = ("admin", "viewer")
SESSION_DAYS = 7
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used_at TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
"""


@contextmanager
def _auth_connect(db_path: Path):
    with _connect(db_path) as conn:
        conn.executescript(AUTH_SCHEMA)
        yield conn


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, digest = stored.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate.hex(), digest)


def check_role(role: str) -> None:
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")


def list_users(db_path: Path = DB_PATH) -> list[dict]:
    with _auth_connect(db_path) as conn:
        rows = conn.execute("SELECT username, role, created_at FROM users ORDER BY username").fetchall()
    return [{"username": r[0], "role": r[1], "created_at": r[2]} for r in rows]


def get_user(username: str, db_path: Path = DB_PATH) -> dict | None:
    with _auth_connect(db_path) as conn:
        row = conn.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,)).fetchone()
    return None if row is None else {"username": row[0], "password_hash": row[1], "role": row[2]}


def create_user(username: str, password: str, role: str, db_path: Path = DB_PATH) -> bool:
    check_role(role)
    with _auth_connect(db_path) as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, _now().isoformat()),
        )
    return cur.rowcount > 0


def update_user(username: str, password: str | None = None, role: str | None = None, db_path: Path = DB_PATH) -> bool:
    if role is not None:
        check_role(role)
    with _auth_connect(db_path) as conn:
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone() is None:
            return False
        if password:
            conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(password), username))
        if role:
            conn.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        # force re-login so a role change or password reset takes effect immediately
        conn.execute("DELETE FROM sessions WHERE username = ? AND source = 'local'", (username,))
    return True


def delete_user(username: str, db_path: Path = DB_PATH) -> bool:
    with _auth_connect(db_path) as conn:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.execute("DELETE FROM sessions WHERE username = ? AND source = 'local'", (username,))
    return cur.rowcount > 0


def create_session(username: str, role: str, source: str, db_path: Path = DB_PATH) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()
    with _auth_connect(db_path) as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, username, role, source, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (_sha256(token), username, role, source, now.isoformat(), (now + timedelta(days=SESSION_DAYS)).isoformat()),
        )
    return token


def get_session(token: str, db_path: Path = DB_PATH) -> dict | None:
    with _auth_connect(db_path) as conn:
        row = conn.execute(
            "SELECT username, role, source FROM sessions WHERE token_hash = ? AND expires_at > ?",
            (_sha256(token), _now().isoformat()),
        ).fetchone()
    return None if row is None else {"username": row[0], "role": row[1], "source": row[2]}


def delete_session(token: str, db_path: Path = DB_PATH) -> None:
    with _auth_connect(db_path) as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_sha256(token),))


def list_tokens(db_path: Path = DB_PATH) -> list[dict]:
    with _auth_connect(db_path) as conn:
        rows = conn.execute("SELECT id, name, role, created_at, last_used_at FROM api_tokens ORDER BY id").fetchall()
    return [{"id": r[0], "name": r[1], "role": r[2], "created_at": r[3], "last_used_at": r[4]} for r in rows]


def create_token(name: str, role: str, db_path: Path = DB_PATH) -> tuple[int, str]:
    check_role(role)
    token = f"rpy_{secrets.token_urlsafe(32)}"
    with _auth_connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO api_tokens (name, token_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (name, _sha256(token), role, _now().isoformat()),
        )
    return cur.lastrowid, token


def get_token(token: str, db_path: Path = DB_PATH) -> dict | None:
    token_hash = _sha256(token)
    with _auth_connect(db_path) as conn:
        row = conn.execute("SELECT id, name, role FROM api_tokens WHERE token_hash = ?", (token_hash,)).fetchone()
        if row is not None:
            conn.execute("UPDATE api_tokens SET last_used_at = ? WHERE id = ?", (_now().isoformat(), row[0]))
    return None if row is None else {"id": row[0], "name": row[1], "role": row[2]}


def delete_token(token_id: int, db_path: Path = DB_PATH) -> bool:
    with _auth_connect(db_path) as conn:
        cur = conn.execute("DELETE FROM api_tokens WHERE id = ?", (token_id,))
    return cur.rowcount > 0


def get_setting(key: str, default: dict | None = None, db_path: Path = DB_PATH) -> dict:
    with _auth_connect(db_path) as conn:
        row = conn.execute("SELECT data FROM settings WHERE key = ?", (key,)).fetchone()
    return dict(default or {}) if row is None else json.loads(row[0])


def save_setting(key: str, data: dict, db_path: Path = DB_PATH) -> None:
    with _auth_connect(db_path) as conn:
        conn.execute(
            "INSERT INTO settings (key, data) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET data = excluded.data",
            (key, json.dumps(data)),
        )
