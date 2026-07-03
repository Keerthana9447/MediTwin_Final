"""
Integration tests — /api/v1/auth/* endpoints, full HTTP round trip
via FastAPI's TestClient (in-process, no real network/server needed).
"""
from __future__ import annotations


class TestRegister:
    def test_register_succeeds_and_returns_token(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "name": "New User", "email": "new@test.com",
            "password": "SecurePass123", "role": "patient",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        assert body["role"] == "patient"
        assert body["user_id"].startswith("USR-")

    def test_register_rejects_duplicate_email(self, client):
        payload = {"name": "Dup", "email": "dup@test.com", "password": "SecurePass123", "role": "patient"}
        first = client.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201

        second = client.post("/api/v1/auth/register", json=payload)
        assert second.status_code == 400
        assert "already registered" in second.json()["detail"].lower()

    def test_register_rejects_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "name": "Weak", "email": "weak@test.com",
            "password": "short", "role": "patient",   # < 8 chars, fails Pydantic Field(min_length=8)
        })
        assert resp.status_code == 422

    def test_register_rejects_short_name(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "name": "A", "email": "shortname@test.com",
            "password": "SecurePass123", "role": "patient",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_succeeds_with_correct_credentials(self, client):
        client.post("/api/v1/auth/register", json={
            "name": "Login Test", "email": "login@test.com",
            "password": "SecurePass123", "role": "patient",
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "login@test.com", "password": "SecurePass123",
        })
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_login_fails_with_wrong_password(self, client):
        client.post("/api/v1/auth/register", json={
            "name": "Login Test", "email": "login2@test.com",
            "password": "SecurePass123", "role": "patient",
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "login2@test.com", "password": "WrongPassword",
        })
        assert resp.status_code == 401

    def test_login_fails_for_unknown_email(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@nowhere.com", "password": "SecurePass123",
        })
        assert resp.status_code == 401


class TestMeAndRefresh:
    def test_me_returns_current_user_with_valid_token(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "patient@meditwin-test.com"
        assert body["role"] == "patient"

    def test_me_rejects_missing_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)  # HTTPBearer raises 403 when header absent

    def test_me_rejects_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert resp.status_code == 401

    def test_refresh_issues_new_valid_token(self, client, auth_headers):
        resp = client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert resp.status_code == 200
        new_token = resp.json()["access_token"]
        assert new_token

        # New token should itself be usable on a protected route
        verify = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert verify.status_code == 200


class TestPersistenceAcrossRequests:
    def test_user_created_in_one_request_is_loginable_in_next(self, client):
        """Proves SQLite persistence works across separate request/response cycles,
        not just within one Python object's lifetime (the old dict bug class)."""
        client.post("/api/v1/auth/register", json={
            "name": "Persist Check", "email": "persist@test.com",
            "password": "SecurePass123", "role": "doctor",
        })
        # Separate, later request — simulates a different request handling the login
        resp = client.post("/api/v1/auth/login", json={
            "email": "persist@test.com", "password": "SecurePass123",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "doctor"
