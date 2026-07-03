"""
MediTwin AI — ML Validation Engine Router
═══════════════════════════════════════════════════════════════
Serves the trained models from ml/train_models.py. Runs alongside
(not instead of) the existing clinical_risk_service — every
prediction can be cross-validated against the clinical engine's
score for the same condition.
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    CrossValidationResponse, MLModelMetrics, MLPredictionResponse, MLPredictRequest,
)
from routers.auth import get_current_user
from services.ml_inference_service import MLInferenceService, get_ml_inference_service

router = APIRouter()

# Maps the ML module's short keys to the clinical_risk_service's full disease names
_CLINICAL_NAME = {"diabetes": "Diabetes", "heart": "Heart Disease", "stroke": None}  # stroke has no clinical-engine counterpart


def _bmi(wt: float, ht: float) -> float:
    return round(wt / ((ht / 100) ** 2), 1) if ht > 0 else 0.0


@router.get("/metrics", response_model=dict[str, MLModelMetrics])
async def get_all_metrics(
    user: dict = Depends(get_current_user),
    ml:   MLInferenceService = Depends(get_ml_inference_service),
) -> dict[str, MLModelMetrics]:
    """Returns full evaluation metrics (accuracy/F1/ROC-AUC/confusion matrix/ROC curve) for all 3 trained models."""
    all_meta = ml.get_all_metadata()
    return {
        key: MLModelMetrics(
            **{k: v for k, v in meta.items() if k != "metrics"},
            **meta["metrics"],
        )
        for key, meta in all_meta.items()
    }


@router.get("/metrics/{disease}", response_model=MLModelMetrics)
async def get_metrics(
    disease: str,
    user: dict = Depends(get_current_user),
    ml:   MLInferenceService = Depends(get_ml_inference_service),
) -> MLModelMetrics:
    """Full evaluation metrics for a single disease model."""
    try:
        meta = ml.get_metadata(disease)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return MLModelMetrics(**{k: v for k, v in meta.items() if k != "metrics"}, **meta["metrics"])


@router.post("/predict/{disease}", response_model=MLPredictionResponse)
async def predict(
    disease: str,
    body: MLPredictRequest,
    user: dict = Depends(get_current_user),
    ml:   MLInferenceService = Depends(get_ml_inference_service),
) -> MLPredictionResponse:
    """Real trained-model prediction + explanation (SHAP or permutation-importance fallback)."""
    profile = body.patient_profile.model_dump()
    profile["vitals"]["bmi"] = _bmi(profile["vitals"]["weight"], profile["vitals"]["height"])
    try:
        result = ml.predict(disease, profile)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return MLPredictionResponse(**result)


@router.post("/cross-validate/{disease}", response_model=CrossValidationResponse)
async def cross_validate(
    disease: str,
    body: MLPredictRequest,
    user: dict = Depends(get_current_user),
    ml:   MLInferenceService = Depends(get_ml_inference_service),
) -> CrossValidationResponse:
    """
    Compares the trained ML model's prediction against the existing
    clinical_risk_service score for the same condition. Stroke has no
    clinical-engine counterpart (FINDRISC/Framingham don't cover it),
    so cross-validation is only meaningful for diabetes and heart disease.
    """
    clinical_name = _CLINICAL_NAME.get(disease)
    if clinical_name is None:
        raise HTTPException(400, f"No clinical-engine counterpart exists for '{disease}' — cross-validation unavailable")

    profile = body.patient_profile.model_dump()
    profile["vitals"]["bmi"] = _bmi(profile["vitals"]["weight"], profile["vitals"]["height"])
    try:
        result = ml.cross_validate(disease, clinical_name, profile)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return CrossValidationResponse(**result)
