"""
Integration tests — /api/v1/ml/* endpoints (trained model metrics + predictions),
plus a model-quality regression test that guards against silently shipping a
retrained model that's worse than what we benchmarked.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

MODELS_DIR = Path(__file__).parent.parent / "ml" / "models"

# Minimum acceptable ROC-AUC per disease — if a future retrain drops below
# this, CI should fail loudly rather than silently ship a worse model.
# Thresholds set ~0.03 below our last validated run (see metadata.json).
MIN_ROC_AUC = {
    "diabetes": 0.82,   # Pima Indians dataset — GBM achieves 0.831 on sklearn 1.6.0
    "heart": 0.88,
    "stroke": 0.88,
}


class TestMLMetricsEndpoint:
    def test_get_all_metrics_requires_auth(self, client):
        resp = client.get("/api/v1/ml/metrics")
        assert resp.status_code in (401, 403)

    def test_get_all_metrics_returns_three_diseases(self, client, auth_headers):
        resp = client.get("/api/v1/ml/metrics", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"diabetes", "heart", "stroke"}

    def test_diabetes_metrics_shape(self, client, auth_headers):
        resp = client.get("/api/v1/ml/metrics/diabetes", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["disease_key"] == "diabetes"
        assert 0.0 <= body["roc_auc"] <= 1.0
        assert 0.0 <= body["accuracy"] <= 1.0
        assert body["n_samples"] > 0
        assert "confusion_matrix" in body
        assert set(body["confusion_matrix"].keys()) == {"tn", "fp", "fn", "tp"}

    def test_unknown_disease_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/ml/metrics/not_a_real_disease", headers=auth_headers)
        assert resp.status_code == 404


@pytest.mark.parametrize("disease", ["diabetes", "heart", "stroke"])
def test_saved_model_meets_minimum_roc_auc(disease):
    """
    Regression guard: reads the actual saved metadata.json for each trained
    model (not a mock) and asserts ROC-AUC hasn't regressed below our last
    known-good benchmark. Run this after every `python train_models.py`
    before deploying — catches "retrained on bad data, AUC silently dropped"
    bugs that no amount of manual eyeballing reliably catches.
    """
    meta_path = MODELS_DIR / disease / "metadata.json"
    assert meta_path.exists(), f"No trained model metadata found for '{disease}' — run train_models.py first"

    with open(meta_path) as f:
        meta = json.load(f)

    roc_auc = meta["metrics"]["roc_auc"]
    assert roc_auc >= MIN_ROC_AUC[disease], (
        f"{disease} model ROC-AUC regressed: {roc_auc:.4f} < required {MIN_ROC_AUC[disease]}"
    )


@pytest.mark.parametrize("disease", ["diabetes", "heart", "stroke"])
def test_saved_model_metadata_has_required_provenance_fields(disease):
    """
    Every model bundle must self-report where its training data came from
    (local_file / downloaded / offline_fallback) so the frontend/judges can
    never mistake fallback-mode numbers for a genuine benchmark result.
    """
    meta_path = MODELS_DIR / disease / "metadata.json"
    with open(meta_path) as f:
        meta = json.load(f)

    assert meta["data_source"] in ("local_file", "downloaded", "offline_fallback")
    assert meta["dataset_name"]
    assert meta["n_samples"] > 0
    assert "global_feature_importance" in meta
    assert len(meta["global_feature_importance"]) > 0
