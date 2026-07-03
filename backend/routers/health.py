"""MediTwin AI — Health Data Router"""
from __future__ import annotations
import random
from datetime import UTC, datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends
from models.schemas import VitalsInput
from routers.auth import get_current_user

router   = APIRouter()
_records: dict[str, list[dict]] = {}


@router.post("/vitals", status_code=201)
async def record_vitals(vitals: VitalsInput, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    uid = user["user_id"]
    bmi = round(vitals.weight / ((vitals.height / 100) ** 2), 1)
    rec = {
        "timestamp": datetime.now(UTC).isoformat(),
        "heart_rate": vitals.heart_rate, "systolic_bp": vitals.systolic_bp,
        "diastolic_bp": vitals.diastolic_bp, "spo2": vitals.spo2,
        "temperature": vitals.temperature, "glucose": vitals.glucose, "bmi": bmi,
    }
    _records.setdefault(uid, []).append(rec)
    alerts: list[str] = []
    if vitals.systolic_bp > 140: alerts.append("High blood pressure detected")
    if vitals.spo2 < 92:         alerts.append("Critical SpO2 — seek immediate medical attention")
    if vitals.glucose > 200:     alerts.append("High glucose — emergency management needed")
    if vitals.heart_rate > 120:  alerts.append("Tachycardia detected")
    return {"status": "recorded", "bmi": bmi, "alerts": alerts}


@router.get("/vitals/live")
async def live_vitals(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rng = random.Random()
    return {
        "timestamp":      datetime.now(UTC).isoformat(),
        "heart_rate":     rng.randint(68, 85),
        "systolic_bp":    rng.randint(118, 132),
        "diastolic_bp":   rng.randint(76, 86),
        "spo2":           round(rng.uniform(95.5, 98.5), 1),
        "temperature":    round(rng.uniform(97.8, 99.2), 1),
        "steps_today":    rng.randint(2000, 8500),
        "calories_burned":rng.randint(1400, 2200),
        "hydration_ml":   rng.randint(800, 2000),
    }


@router.get("/vitals/history")
async def vitals_history(days: int = 30, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    uid    = user["user_id"]
    cutoff = datetime.now(UTC) - timedelta(days=days)
    recs   = [r for r in _records.get(uid, [])
              if datetime.fromisoformat(r["timestamp"]) >= cutoff]
    return {"records": recs, "count": len(recs)}


@router.get("/timeline")
async def timeline(months: int = 6, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    now, data = datetime.now(UTC), []
    for i in range(months, 0, -1):
        dt = now - timedelta(days=30 * i)
        sc = 63 + (months - i) * 1.5 + random.uniform(-1, 1)
        data.append({
            "month":        dt.strftime("%b"), "year": dt.year,
            "health_score": round(max(50, min(95, sc))),
            "diabetes_risk":round(46 - (months-i)*1.2 + random.uniform(-1, 1), 1),
            "heart_risk":   round(28 - (months-i)*0.8 + random.uniform(-0.5, 0.5), 1),
            "stress_level": round(80 - (months-i)*2   + random.uniform(-2, 2), 1),
            "blood_pressure":round(136 - (months-i)*1.5 + random.uniform(-1, 1), 1),
        })
    return {"timeline": data, "months": months}


@router.get("/bmi")
async def bmi(weight_kg: float, height_cm: float, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    b   = round(weight_kg / ((height_cm / 100) ** 2), 1)
    cat = "Underweight" if b < 18.5 else "Normal" if b < 25 else "Overweight" if b < 30 else "Obese"
    return {"bmi": b, "category": cat}
