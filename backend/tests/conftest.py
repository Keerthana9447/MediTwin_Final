"""
MediTwin AI — Shared pytest fixtures
═══════════════════════════════════════════════════════════════
Key design choice: every test run gets its OWN throwaway SQLite
file (tmp_path), so tests never pollute backend/meditwin.db and
can run in parallel / repeatedly without manual cleanup.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow `pytest` to be run from backend/ or repo root
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    """Point db.py at a fresh temp SQLite file for this test only."""
    import db
    db_file = tmp_path / "test_meditwin.db"
    monkeypatch.setattr(db, "DB_PATH", db_file)
    db.init_db()
    return db


@pytest.fixture()
def client(test_db, monkeypatch):
    """FastAPI TestClient wired to the isolated test_db fixture."""
    # Use a fixed, predictable secret for token tests
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-not-for-production")
    monkeypatch.setenv("ALGORITHM", "HS256")

    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    """Registers a fresh user and returns ready-to-use Authorization headers."""
    resp = client.post("/api/v1/auth/register", json={
        "name": "Test Patient",
        "email": "patient@meditwin-test.com",
        "password": "SecurePass123",
        "role": "patient",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
