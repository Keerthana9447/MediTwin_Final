"""
Unit tests — auth.py pure functions (password hashing, JWT tokens).
No DB, no HTTP — fast, isolated, run in milliseconds.
"""
from __future__ import annotations

import pytest


def _import_auth():
    from routers import auth
    return auth


class TestPasswordHashing:
    def test_hash_password_returns_salt_dollar_hash_format(self):
        auth = _import_auth()
        hashed = auth.hash_password("MySecurePass123")
        assert "$" in hashed
        salt, digest = hashed.split("$", 1)
        assert len(salt) == 32          # 16 bytes hex-encoded
        assert len(digest) == 64        # SHA-256 hex digest

    def test_same_password_produces_different_hashes(self):
        """Random salt per call — two hashes of the same password must differ."""
        auth = _import_auth()
        h1 = auth.hash_password("password123")
        h2 = auth.hash_password("password123")
        assert h1 != h2

    def test_verify_password_succeeds_with_correct_password(self):
        auth = _import_auth()
        hashed = auth.hash_password("correct-horse-battery-staple")
        assert auth.verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_password_fails_with_wrong_password(self):
        auth = _import_auth()
        hashed = auth.hash_password("correct-horse-battery-staple")
        assert auth.verify_password("wrong-password", hashed) is False

    def test_verify_password_handles_malformed_stored_hash(self):
        """Should never raise — malformed stored data must fail closed."""
        auth = _import_auth()
        assert auth.verify_password("anything", "not-a-valid-hash-format") is False


class TestJWTTokens:
    def test_create_access_token_round_trips_via_decode(self):
        auth = _import_auth()
        token = auth.create_access_token({"sub": "user@test.com", "user_id": "USR-00001", "role": "patient"})
        decoded = auth.decode_token(token)
        assert decoded["sub"] == "user@test.com"
        assert decoded["user_id"] == "USR-00001"
        assert decoded["role"] == "patient"
        assert "exp" in decoded

    def test_decode_token_rejects_garbage_token(self):
        auth = _import_auth()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            auth.decode_token("this.is.not.a.valid.jwt")
        assert exc_info.value.status_code == 401

    def test_decode_token_rejects_tampered_signature(self):
        auth = _import_auth()
        from fastapi import HTTPException
        token = auth.create_access_token({"sub": "user@test.com", "user_id": "X", "role": "patient"})
        tampered = token[:-4] + "abcd"   # corrupt the signature segment
        with pytest.raises(HTTPException):
            auth.decode_token(tampered)
