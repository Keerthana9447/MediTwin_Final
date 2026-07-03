"""
Integration tests — app-level health/root endpoints.
"""
from __future__ import annotations


def test_root_endpoint_reports_operational_status(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "MediTwin AI"
    assert body["status"] == "operational"


def test_health_check_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_docs_are_served(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_protected_route_without_token_is_rejected(client):
    """Sanity check that auth is actually enforced on a representative protected route."""
    resp = client.get("/api/v1/health/vitals/live")
    assert resp.status_code in (401, 403)
