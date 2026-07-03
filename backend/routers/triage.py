"""MediTwin AI — Emergency Triage Router"""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from models.schemas import TriageLevel, TriagePatient, TriageScore
from routers.auth import get_current_user

router = APIRouter()
_queue: dict[str, list[dict]] = {}


def _score(p: TriagePatient) -> tuple[int, TriageLevel, str, str]:
    """Returns (score 0-100, level, action, alert). All 4 values."""
    sc, reasons = 0.0, []
    v = p.vitals

    if   v.systolic_bp >= 180: sc += 25; reasons.append("Hypertensive crisis")
    elif v.systolic_bp >= 160: sc += 18; reasons.append("Stage 2 hypertension")
    elif v.systolic_bp >= 140: sc += 10; reasons.append("Stage 1 hypertension")
    elif v.systolic_bp < 90:   sc += 20; reasons.append("Hypotension")

    if   v.spo2 < 88:  sc += 20; reasons.append("Critical hypoxia")
    elif v.spo2 < 92:  sc += 15; reasons.append("Low SpO2")
    elif v.spo2 < 95:  sc += 8

    if   v.glucose > 400: sc += 20; reasons.append("Diabetic emergency")
    elif v.glucose > 300: sc += 15; reasons.append("Severe hyperglycemia")
    elif v.glucose > 200: sc += 8
    elif v.glucose < 60:  sc += 18; reasons.append("Critical hypoglycemia")
    elif v.glucose < 70:  sc += 10; reasons.append("Hypoglycemia")

    if   v.heart_rate > 150 or v.heart_rate < 40:   sc += 20; reasons.append("Critical arrhythmia")
    elif v.heart_rate > 120 or v.heart_rate < 50:   sc += 12; reasons.append("Abnormal HR")
    elif v.heart_rate > 100: sc += 6

    if v.temperature > 104: sc += 10; reasons.append("High fever")
    elif v.temperature < 95: sc += 10; reasons.append("Hypothermia")

    if p.age > 70:   sc += 5
    elif p.age > 60: sc += 3

    final = min(100, int(round(sc)))

    if   final >= 75: lvl, action = TriageLevel.CRITICAL, "Immediate intervention — alert physician NOW"
    elif final >= 50: lvl, action = TriageLevel.HIGH,     "Priority assessment within 10 minutes"
    elif final >= 25: lvl, action = TriageLevel.MEDIUM,   "Monitor and assess within 30 minutes"
    else:             lvl, action = TriageLevel.LOW,       "Routine care — standard queue"

    alert = "; ".join(reasons[:3]) if reasons else "Stable presentation"
    return final, lvl, action, alert


@router.post("/admit", response_model=TriageScore, status_code=201)
async def admit(patient: TriagePatient, user: dict = Depends(get_current_user)) -> TriageScore:
    sc, lvl, action, alert = _score(patient)
    hid = user.get("user_id", "default")
    q   = _queue.setdefault(hid, [])
    q.append({**patient.model_dump(), "triage_score": sc, "triage_level": lvl.value,
               "admitted_at": datetime.now(UTC).isoformat(),
               "recommended_action": action, "alert_message": alert})
    _queue[hid] = sorted(q, key=lambda x: x["triage_score"], reverse=True)
    rank = next(i+1 for i, p in enumerate(_queue[hid]) if p["patient_id"] == patient.patient_id)
    return TriageScore(patient_id=patient.patient_id, name=patient.name,
                       triage_score=sc, triage_level=lvl, priority_rank=rank,
                       alert_message=alert, recommended_action=action)


@router.get("/queue")
async def get_queue(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    hid = user.get("user_id", "default")
    q   = _queue.get(hid, [])
    return {
        "queue":  [{"rank": i+1, **p} for i, p in enumerate(q)],
        "total":  len(q),
        "counts": {lvl: sum(1 for p in q if p["triage_level"] == lvl)
                   for lvl in ["critical","high","medium","low"]},
    }


@router.delete("/discharge/{patient_id}")
async def discharge(patient_id: str, user: dict = Depends(get_current_user)) -> dict:
    hid    = user.get("user_id", "default")
    before = len(_queue.get(hid, []))
    _queue[hid] = [p for p in _queue.get(hid, []) if p["patient_id"] != patient_id]
    if len(_queue.get(hid, [])) == before:
        raise HTTPException(404, f"Patient {patient_id} not found in queue")
    return {"status": "discharged", "patient_id": patient_id}


@router.get("/stats")
async def stats(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    hid = user.get("user_id", "default")
    q   = _queue.get(hid, [])
    if not q:
        return {"total": 0, "message": "Queue is empty"}
    return {"total_patients": len(q),
            "average_score": round(sum(p["triage_score"] for p in q) / len(q), 1),
            "critical_count": sum(1 for p in q if p["triage_level"] == "critical")}
