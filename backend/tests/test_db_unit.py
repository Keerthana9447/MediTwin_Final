"""
Unit tests — db.py (SQLite persistence layer).
Uses the `test_db` fixture from conftest.py, which points db.py at a
throwaway temp file so these tests never touch the real meditwin.db.
"""
from __future__ import annotations

import sqlite3

import pytest


class TestUserPersistence:
    def test_init_db_creates_users_table(self, test_db):
        with test_db.get_conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            ).fetchone()
        assert row is not None

    def test_get_user_by_email_returns_none_when_absent(self, test_db):
        assert test_db.get_user_by_email("nobody@nowhere.com") is None

    def test_create_user_then_fetch_round_trips_all_fields(self, test_db):
        test_db.create_user("USR-00001", "Alice", "alice@test.com", "hash:abc", "patient")
        user = test_db.get_user_by_email("alice@test.com")
        assert user["id"] == "USR-00001"
        assert user["name"] == "Alice"
        assert user["email"] == "alice@test.com"
        assert user["hashed_password"] == "hash:abc"
        assert user["role"] == "patient"
        assert "created_at" in user

    def test_duplicate_email_raises_integrity_error(self, test_db):
        test_db.create_user("USR-00001", "Alice", "dup@test.com", "hash:1", "patient")
        with pytest.raises(sqlite3.IntegrityError):
            test_db.create_user("USR-00002", "Alice Clone", "dup@test.com", "hash:2", "patient")

    def test_count_users_increments_correctly(self, test_db):
        assert test_db.count_users() == 0
        test_db.create_user("USR-00001", "A", "a@test.com", "h", "patient")
        assert test_db.count_users() == 1
        test_db.create_user("USR-00002", "B", "b@test.com", "h", "doctor")
        assert test_db.count_users() == 2

    def test_data_persists_across_reconnect(self, test_db):
        """The whole point of swapping dict -> SQLite: survive a process restart."""
        test_db.create_user("USR-00001", "Persistent Pete", "pete@test.com", "h", "patient")

        # Simulate a fresh connection (e.g. after server restart) — same DB_PATH file
        with test_db.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", ("pete@test.com",)).fetchone()
        assert row is not None
        assert row["name"] == "Persistent Pete"
