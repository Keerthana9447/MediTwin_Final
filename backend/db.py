"""
MediTwin AI — Lightweight Persistence Layer
═══════════════════════════════════════════════════════════════
SQLite via the Python stdlib `sqlite3` module — zero extra
dependencies, zero external services to install/run, but REAL
persistence: data survives process restarts, unlike the previous
in-memory dict.

This is intentionally the smallest possible step up from "no
database" while keeping a clean migration path:
  - All access goes through this one module (repository pattern).
  - Swapping to PostgreSQL later means changing only this file —
    routers/services never touch SQL directly.
  - Schema is simple and normalized enough to map 1:1 onto a
    Postgres table if/when we move to Firebase/Postgres in
    production (see README "Production Data Layer" section).

DB file: backend/meditwin.db (gitignored; created on first run)
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).parent / "meditwin.db"

# SQLite connections aren't thread-safe by default; FastAPI can serve
# requests on different threads, so we guard with a lock + one
# connection per call (cheap for SQLite, simplest correct approach
# for an MVP-scale app).
_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent read/write
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db() -> None:
    """Create tables if they don't exist. Call once at app startup."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                email           TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role            TEXT NOT NULL DEFAULT 'patient',
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)


# ── User repository functions ─────────────────────────────────────
def get_user_by_email(email: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def create_user(user_id: str, name: str, email: str, hashed_password: str, role: str) -> dict[str, Any]:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id, name, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, hashed_password, role),
        )
    return {"id": user_id, "name": name, "email": email, "hashed_password": hashed_password, "role": role}


def count_users() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        return int(row["n"])
