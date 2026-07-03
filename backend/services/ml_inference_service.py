"""
MediTwin AI — ML Inference Service
═══════════════════════════════════════════════════════════════
Loads the artifacts produced by ml/train_models.py and serves live
predictions. Self-healing: if artifacts are missing (first run, or
a fresh clone before anyone ran the training script), it trains
on the fly using ml/datasets.py's same real-download-or-fallback
loaders, so the API never hard-fails due to a missing training step.

Each disease has its own patient-profile → feature-vector mapper,
since the three datasets use different schemas (Pima's 8 numeric
columns vs. Cleveland's 13 clinical columns vs. Stroke's mixed
numeric/categorical one-hot columns). The mapper translates
MediTwin's existing PatientProfile fields into each dataset's
exact expected feature order — this is the glue that lets one
unified patient profile drive three independently-trained models.
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.datasets import LOADERS
from ml.train_models import train_one

logger = logging.getLogger("meditwin.ml.inference")
MODELS_DIR = Path(__file__).parent.parent / "ml" / "models"

DISEASE_DISPLAY_NAMES = {"diabetes": "Diabetes", "heart": "Heart Disease", "stroke": "Stroke"}


def _bmi(weight_kg: float, height_cm: float) -> float:
    return round(weight_kg / ((height_cm / 100) ** 2), 1) if height_cm else 25.0


def _has_history(profile: dict[str, Any], *keywords: str) -> bool:
    hx = [h.lower() for h in profile.get("family_history", []) + profile.get("medical_history", [])]
    return any(any(kw in h for kw in keywords) for h in hx)


def _map_diabetes(profile: dict[str, Any]) -> list[float]:
    v, lif = profile.get("vitals", {}), profile.get("lifestyle", {})
    age = profile.get("age", 35)
    return [
        0.0,  # Pregnancies — not collected in MediTwin's profile; assume nulliparous/unknown baseline
        float(v.get("glucose", 90)),
        float(v.get("diastolic_bp", 80)) + 4,  # proxy: dataset's "BloodPressure" ≈ diastolic in this schema
        25.0,  # SkinThickness — not collected; population median
        85.0,  # Insulin — not collected; population median
        float(v.get("bmi", _bmi(v.get("weight", 70), v.get("height", 170)))),
        0.5 if _has_history(profile, "diabetes", "t2dm") else 0.2,  # DiabetesPedigreeFunction proxy
        float(age),
    ]


def _map_heart(profile: dict[str, Any]) -> list[float]:
    v, lif = profile.get("vitals", {}), profile.get("lifestyle", {})
    age = profile.get("age", 35)
    sex = 1 if profile.get("gender", "").lower() == "male" else 0
    return [
        float(age), float(sex),
        2.0,  # cp (chest pain type) — not collected; assume "non-anginal" baseline (2)
        float(v.get("systolic_bp", 120)),
        200.0,  # chol — not collected; population median
        1 if v.get("glucose", 90) > 126 else 0,  # fbs proxy from fasting glucose
        0.0,  # restecg — not collected; assume normal
        float(220 - age - (10 if lif.get("smoking") else 0)),  # thalach proxy: age-predicted max HR
        1 if lif.get("smoking", False) else 0,  # exang proxy
        1.0 if lif.get("stress_level", 5) >= 7 else 0.3,  # oldpeak proxy
        1.0,  # slope — not collected; assume flat/normal
        1 if _has_history(profile, "heart", "cardiac", "cvd") else 0,  # ca proxy
        3.0,  # thal — not collected; assume normal (3)
    ]


def _map_stroke(profile: dict[str, Any], feature_names: list[str]) -> list[float]:
    """Stroke model features are one-hot encoded — build a dict then align to feature_names order."""
    v, lif = profile.get("vitals", {}), profile.get("lifestyle", {})
    age = profile.get("age", 35)
    gender = profile.get("gender", "male").lower()

    row: dict[str, float] = {
        "age": float(age),
        "hypertension": 1.0 if v.get("systolic_bp", 120) >= 140 else 0.0,
        "heart_disease": 1.0 if _has_history(profile, "heart", "cardiac") else 0.0,
        "avg_glucose_level": float(v.get("glucose", 90)),
        "bmi": float(v.get("bmi", _bmi(v.get("weight", 70), v.get("height", 170)))),
        f"gender_{'Male' if gender == 'male' else 'Female'}": 1.0,
        "ever_married_Yes": 1.0 if age >= 25 else 0.0,
        "work_type_Private": 1.0,
        "Residence_type_Urban": 1.0,
        "smoking_status_smokes" if lif.get("smoking") else "smoking_status_never smoked": 1.0,
    }
    return [row.get(name, 0.0) for name in feature_names]


_MAPPERS = {
    "diabetes": lambda profile, feature_names: _map_diabetes(profile),
    "heart":    lambda profile, feature_names: _map_heart(profile),
    "stroke":   lambda profile, feature_names: _map_stroke(profile, feature_names),
}


class MLInferenceService:
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def _load_or_train(self, disease: str) -> dict[str, Any]:
        if disease in self._cache:
            return self._cache[disease]

        out_dir = MODELS_DIR / disease
        metadata_path = out_dir / "metadata.json"

        if metadata_path.exists():
            import json
            model = joblib.load(out_dir / "model.pkl")
            scaler = joblib.load(out_dir / "scaler.pkl")
            explainer = joblib.load(out_dir / "explainer.pkl")
            with open(metadata_path) as f:
                metadata = json.load(f)
            logger.info("Loaded cached %s model (%s)", disease, metadata["best_model"])
        else:
            logger.info("No cached model for %s — training now (first run)", disease)
            metadata = train_one(disease, save=True)
            model = joblib.load(out_dir / "model.pkl")
            scaler = joblib.load(out_dir / "scaler.pkl")
            explainer = joblib.load(out_dir / "explainer.pkl")

        bundle = {"model": model, "scaler": scaler, "explainer": explainer, "metadata": metadata}
        self._cache[disease] = bundle
        return bundle

    def get_metadata(self, disease: str) -> dict[str, Any]:
        return self._load_or_train(disease)["metadata"]

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        return {d: self.get_metadata(d) for d in LOADERS}

    def predict(self, disease: str, patient_profile: dict[str, Any]) -> dict[str, Any]:
        bundle = self._load_or_train(disease)
        model, scaler, explainer, metadata = bundle["model"], bundle["scaler"], bundle["explainer"], bundle["metadata"]
        feature_names = metadata["feature_names"]

        raw_row = np.array(_MAPPERS[disease](patient_profile, feature_names), dtype=float).reshape(1, -1)
        scaled_row = scaler.transform(raw_row)

        proba = float(model.predict_proba(scaled_row)[0][1])
        contributions, method = explainer.explain_prediction(scaled_row[0], top_k=5, x_row_raw=raw_row[0])

        note = (
            "ML contributions are computed relative to the TRAINING POPULATION's average "
            "(these are risk-enriched screening datasets, so that average is already elevated "
            "vs. general clinical norms) — a value can show 'decreases risk' even if it's "
            "clinically abnormal, if it's still below this specific cohort's baseline. This is "
            "exact model behavior, not an error. Compare against the Clinical Engine's absolute "
            "threshold-based score (FINDRISC/Framingham) for the complementary reference frame."
            if method.startswith("Linear Coefficient") else
            "Feature contributions are exact Shapley-value attributions from the trained model."
            if method.startswith("SHAP") else
            "Feature contributions approximate directional influence; install `shap` for exact "
            "Shapley-value attribution."
        )

        return {
            "disease": metadata["disease"],
            "probability_pct": round(proba * 100, 1),
            "model_used": metadata["best_model"],
            "dataset_name": metadata["dataset_name"],
            "data_source": metadata["data_source"],
            "model_accuracy": metadata["metrics"]["accuracy"],
            "model_roc_auc": metadata["metrics"]["roc_auc"],
            "explanation_method": method,
            "interpretation_note": note,
            "top_factors": [
                {
                    "feature": c.feature, "value": c.value,
                    "contribution": c.contribution, "direction": c.direction,
                }
                for c in contributions
            ],
        }


    def cross_validate(self, disease_key: str, clinical_disease_name: str, patient_profile: dict[str, Any]) -> dict[str, Any]:
        """
        Compare this ML model's prediction against the existing clinical_risk_service's
        score for the same condition. Two independent reference frames — absolute
        clinical thresholds (FINDRISC/Framingham) vs. population-relative trained model —
        legitimately can disagree; that disagreement is itself diagnostic signal, not noise.
        """
        from services.clinical_risk_service import get_clinical_risk_service

        ml_result = self.predict(disease_key, patient_profile)
        clinical = get_clinical_risk_service()
        clinical_results = clinical.predict_all_risks(patient_profile)
        clinical_match = next((r for r in clinical_results if r.disease == clinical_disease_name), None)

        clinical_pct = clinical_match.probability if clinical_match else None
        ml_pct = ml_result["probability_pct"]
        agreement_delta = None
        agreement_label = "unavailable"

        if clinical_pct is not None:
            agreement_delta = round(abs(clinical_pct - ml_pct), 1)
            if agreement_delta <= 10:
                agreement_label = "high_agreement"
            elif agreement_delta <= 20:
                agreement_label = "moderate_agreement"
            else:
                agreement_label = "discrepancy_review_recommended"

        return {
            "ml_probability_pct": ml_pct,
            "clinical_probability_pct": clinical_pct,
            "clinical_tool": clinical_match.tool_used if clinical_match else None,
            "agreement_delta_points": agreement_delta,
            "agreement_label": agreement_label,
            "ml_details": ml_result,
        }


_instance: MLInferenceService | None = None

def get_ml_inference_service() -> MLInferenceService:
    global _instance
    if _instance is None:
        _instance = MLInferenceService()
    return _instance
