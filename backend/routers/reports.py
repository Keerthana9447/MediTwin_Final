"""MediTwin AI — Medical Report Analyzer Router"""
from __future__ import annotations
import time
from typing import Any
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from models.schemas import AbnormalMetric, ReportAnalysisResponse
from routers.auth import get_current_user
from services.groq_service import GroqService, get_groq_service
from services.ocr_service import OCRService, get_ocr_service

router   = APIRouter()
MAX_SIZE = 10 * 1024 * 1024
ALLOWED  = {"image/jpeg", "image/png", "image/bmp", "application/pdf", "text/plain"}


@router.post("/analyze", response_model=ReportAnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    user: dict        = Depends(get_current_user),
    ocr:  OCRService  = Depends(get_ocr_service),
    groq: GroqService = Depends(get_groq_service),
) -> ReportAnalysisResponse:
    if file.content_type not in ALLOWED:
        raise HTTPException(415, f"Unsupported type: {file.content_type}. Use PDF/JPG/PNG.")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "File too large — max 10 MB")
    t0       = time.monotonic()
    text     = ocr.extract_text(data, file.filename or "report.pdf")
    abnormals = ocr.detect_abnormalities(text)
    analysis  = await groq.analyze_report(text)
    elapsed   = int((time.monotonic() - t0) * 1000)
    metrics   = [
        AbnormalMetric(parameter=a["parameter"], value=a["value"],
                       normal_range=a["normal_range"], severity=a["severity"],
                       interpretation=f"{a['status'].upper()} — clinical review recommended")
        for a in abnormals
    ]
    recs = [ln.strip() for ln in analysis.split("\n")
            if ln.strip() and len(ln.strip()) > 10 and ln.strip()[0].isdigit()]
    risk = ("CRITICAL" if any(m.severity == "critical" for m in metrics)
            else "HIGH" if metrics else "LOW")
    return ReportAnalysisResponse(
        raw_text=text[:2000], abnormal_metrics=metrics,
        ai_interpretation=analysis, risk_assessment=risk,
        recommendations=recs[:8] or ["Consult your physician for full interpretation"],
        confidence_score=min(0.95, 0.75 + len(metrics) * 0.03),
        processing_time_ms=elapsed,
    )


@router.post("/analyze-text")
async def analyze_text(
    body: dict[str, str] = Body(...),
    user: dict            = Depends(get_current_user),
    ocr:  OCRService      = Depends(get_ocr_service),
    groq: GroqService     = Depends(get_groq_service),
) -> dict[str, Any]:
    text = body.get("text", "")
    if not text.strip():
        raise HTTPException(400, "Text cannot be empty")
    t0 = time.monotonic()
    ab = ocr.detect_abnormalities(text)
    ai = await groq.analyze_report(text)
    return {"abnormal_count": len(ab), "abnormalities": ab,
            "ai_analysis": ai, "processing_time_ms": int((time.monotonic()-t0)*1000)}
