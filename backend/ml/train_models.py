"""
MediTwin AI — ML Training Pipeline
═══════════════════════════════════════════════════════════════
Trains Logistic Regression, Random Forest, and Gradient Boosting on
each of the 3 disease datasets (via datasets.py — real download or
local file when available, honest statistical fallback otherwise),
selects the best model per disease by ROC-AUC, computes the full
evaluation suite (accuracy / precision / recall / F1 / ROC-AUC /
confusion matrix / ROC curve points), fits an explainability engine
(real SHAP or permutation-importance fallback — see explainability.py),
and saves everything needed for live inference to ml/models/{disease}/.

Run standalone:
    python train_models.py
Or import and call train_all() / train_one(disease) from the API
startup path for a self-healing "train on first request if missing"
pattern (used by services/ml_inference_service.py).
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))  # allow `python train_models.py` standalone

from ml.datasets import LOADERS
from ml.explainability import ExplainabilityEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("meditwin.ml.train")

MODELS_DIR = Path(__file__).parent / "models"
RANDOM_STATE = 42


def _candidate_models() -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=6, class_weight="balanced",
            random_state=RANDOM_STATE, min_samples_split=8,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.08, random_state=RANDOM_STATE,
        ),
    }


def _evaluate(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, Any]:
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    fpr, tpr, _ = roc_curve(y_test, y_proba)

    # Downsample ROC curve to ~40 points for compact JSON / smooth chart rendering
    if len(fpr) > 40:
        idx = np.linspace(0, len(fpr) - 1, 40).astype(int)
        fpr_plot, tpr_plot = fpr[idx], tpr[idx]
    else:
        fpr_plot, tpr_plot = fpr, tpr

    return {
        "accuracy":  round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1":        round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc":   round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "roc_curve": [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(fpr_plot, tpr_plot)],
    }


def train_one(disease: str, save: bool = True) -> dict[str, Any]:
    """Train, evaluate, explain, and (optionally) persist all artifacts for one disease."""
    if disease not in LOADERS:
        raise ValueError(f"Unknown disease '{disease}'. Choose from {list(LOADERS)}")

    t0 = time.monotonic()
    logger.info("── Training: %s ──", disease)

    X, y, data_meta = LOADERS[disease]()
    feature_names = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X.values, y.values, test_size=0.2, random_state=RANDOM_STATE, stratify=y.values,
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    results: dict[str, dict[str, Any]] = {}
    fitted_models: dict[str, Any] = {}

    for name, model in _candidate_models().items():
        model.fit(X_train_s, y_train)
        metrics = _evaluate(model, X_test_s, y_test)
        results[name] = metrics
        fitted_models[name] = model
        logger.info(
            "  %-20s acc=%.3f  f1=%.3f  roc_auc=%.3f",
            name, metrics["accuracy"], metrics["f1"], metrics["roc_auc"],
        )

    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best_model = fitted_models[best_name]
    best_metrics = results[best_name]
    model_kind = "tree" if best_name in ("random_forest", "gradient_boosting") else "linear"

    logger.info("  → best model: %s (ROC-AUC %.3f)", best_name, best_metrics["roc_auc"])

    explainer = ExplainabilityEngine(best_model, X_train_s, feature_names, model_kind)
    global_importance = explainer.global_feature_importance()

    elapsed_ms = int((time.monotonic() - t0) * 1000)

    bundle = {
        "disease": data_meta["disease"],
        "disease_key": disease,
        "dataset_name": data_meta["dataset_name"],
        "data_source": data_meta["source"],
        "n_samples": data_meta["n_samples"],
        "n_features": data_meta["n_features"],
        "positive_rate": data_meta["positive_rate"],
        "feature_names": feature_names,
        "best_model": best_name,
        "model_kind": model_kind,
        "explainability_method": explainer.method,
        "all_models_compared": {n: {"accuracy": r["accuracy"], "f1": r["f1"], "roc_auc": r["roc_auc"]} for n, r in results.items()},
        "metrics": best_metrics,
        "global_feature_importance": global_importance,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "training_time_ms": elapsed_ms,
    }

    if save:
        out_dir = MODELS_DIR / disease
        out_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, out_dir / "model.pkl")
        joblib.dump(scaler, out_dir / "scaler.pkl")
        joblib.dump(explainer, out_dir / "explainer.pkl")
        with open(out_dir / "metadata.json", "w") as f:
            json.dump(bundle, f, indent=2)
        logger.info("  Saved artifacts → %s", out_dir)

    return bundle


def train_all(save: bool = True) -> dict[str, dict[str, Any]]:
    return {disease: train_one(disease, save=save) for disease in LOADERS}


if __name__ == "__main__":
    logger.info("═" * 60)
    logger.info("MediTwin AI — ML Training Pipeline")
    logger.info("═" * 60)
    all_results = train_all(save=True)
    logger.info("═" * 60)
    logger.info("TRAINING SUMMARY")
    logger.info("═" * 60)
    for disease, bundle in all_results.items():
        logger.info(
            "%-12s | source=%-16s | model=%-19s | acc=%.3f f1=%.3f roc_auc=%.3f | explain=%s",
            bundle["disease"], bundle["data_source"], bundle["best_model"],
            bundle["metrics"]["accuracy"], bundle["metrics"]["f1"], bundle["metrics"]["roc_auc"],
            bundle["explainability_method"],
        )
    logger.info("═" * 60)
    logger.info("Done. Restart the API (or it will self-load on next request) to serve these models.")
