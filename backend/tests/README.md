# MediTwin AI — Backend Test Suite

## Run all tests

```bash
cd backend
pip install -r requirements.txt --prefer-binary
pytest
```

## What's covered

| File | Covers | Type |
|---|---|---|
| `test_auth_unit.py` | Password hashing (PBKDF2), JWT create/decode | Unit (no DB, no HTTP) |
| `test_db_unit.py` | SQLite persistence layer (`db.py`) — create/fetch users, uniqueness, restart-survival | Unit (isolated temp DB) |
| `test_auth_integration.py` | `/api/v1/auth/*` — register, login, `/me`, `/refresh`, duplicate-email rejection, persistence across requests | Integration (FastAPI `TestClient`) |
| `test_app_health.py` | Root `/`, `/health`, `/docs`, auth-required enforcement on a protected route | Integration |
| `test_ml_metrics.py` | `/api/v1/ml/metrics*` endpoints + **model-quality regression test** that reads the real saved `metadata.json` for all 3 trained models and fails the build if ROC-AUC drops below a known-good threshold | Integration + regression |

## Design notes

- **Isolated test DB**: every test gets its own throwaway SQLite file via the `test_db` fixture (`tmp_path`), so running tests never touches or corrupts `backend/meditwin.db`.
- **No mocking the ML models**: `test_ml_metrics.py` reads the actual `ml/models/{disease}/metadata.json` files produced by `train_models.py` — this is a real regression guard, not a unit test against a stub.
- **Run after retraining**: if you re-run `python ml/train_models.py`, run `pytest tests/test_ml_metrics.py` immediately after — it will fail loudly if the new model is worse than our last benchmark (current thresholds: diabetes ≥0.85, heart ≥0.88, stroke ≥0.88 ROC-AUC).

## Coverage gaps (next sprint)

- Other routers (`reports`, `triage`, `family`, `timemachine`, etc.) don't have dedicated test files yet — `auth` and `ml` were prioritized since they're the highest-risk surfaces (security, prediction reliability).
- No load/performance tests.
- No CI workflow file yet (`.github/workflows/test.yml`) — tests currently run manually.
