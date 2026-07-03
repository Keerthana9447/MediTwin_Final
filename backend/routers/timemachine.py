"""MediTwin AI — Health Time Machine Router (MODULE 2)"""
from __future__ import annotations

from models.schemas import TimeMachineRequest, TimeMachineResponse
from routers.auth import get_current_user
from services.groq_service import GroqService, get_groq_service
from services.time_machine_service import TimeMachineService, get_time_machine_service

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.post("/project", response_model=TimeMachineResponse)
async def project_future(
    body: TimeMachineRequest,
    user: dict               = Depends(get_current_user),
    tm:   TimeMachineService = Depends(get_time_machine_service),
    groq: GroqService        = Depends(get_groq_service),
) -> TimeMachineResponse:
    """
    Projects the patient's health 1/5/10 years forward.
    If `apply_prevention` contains action ids, returns the
    "Future B" (with-prevention) scenario instead of status-quo.
    """
    if body.years not in (1, 5, 10):
        raise HTTPException(400, "years must be 1, 5, or 10")

    profile = body.current_profile.model_dump()
    profile["vitals"]["bmi"] = round(
        profile["vitals"]["weight"] / ((profile["vitals"]["height"] / 100) ** 2), 1
    )

    with_prevention = len(body.apply_prevention) > 0
    result = tm.project(profile, body.years, with_prevention=with_prevention)

    scenario = "with_prevention" if with_prevention else "status_quo"

    # AI narrative — the "cinematic" copy
    top_changes = sorted(result["disease_progression"], key=lambda d: abs(d.delta), reverse=True)[:2]
    changes_str = ", ".join(
        f"{d.disease} {'↑' if d.delta > 0 else '↓'}{abs(d.delta)}%" for d in top_changes
    )
    if with_prevention:
        prompt = (
            f"MediTwin Time Machine — 'Future B' scenario for {profile.get('name')}, "
            f"projecting {body.years} years forward WITH sustained preventive habits applied. "
            f"Age {result['current_age']} → {result['future_age']}. "
            f"Health Score {result['current_health_score']} → {result['future_health_score']}. "
            f"Key changes: {changes_str}. "
            "Write an encouraging, cinematic 3-sentence narrative — 'this is the future you can choose'."
        )
    else:
        prompt = (
            f"MediTwin Time Machine — status-quo scenario for {profile.get('name')}, "
            f"projecting {body.years} years forward if current habits continue unchanged. "
            f"Age {result['current_age']} → {result['future_age']}. "
            f"Health Score {result['current_health_score']} → {result['future_health_score']}. "
            f"Key changes: {changes_str}. "
            "Write a vivid but non-alarmist 3-sentence narrative — 'this is where things are headed'."
        )

    try:
        narrative, _ = await groq.chat([{"role": "user", "content": prompt}], max_tokens=180)
    except Exception:
        if with_prevention:
            narrative = (
                f"At age {result['future_age']}, sustained healthy habits keep your health score "
                f"near {result['future_health_score']}/100. {changes_str} — a future you actively chose."
            )
        else:
            narrative = (
                f"At age {result['future_age']}, if current habits continue, your health score "
                f"trends toward {result['future_health_score']}/100. {changes_str} — "
                "small changes now can shift this trajectory."
            )

    return TimeMachineResponse(
        patient_id=user.get("user_id", "anon"),
        current_age=result["current_age"],
        future_age=result["future_age"],
        years_projected=body.years,
        current_health_score=result["current_health_score"],
        future_health_score=result["future_health_score"],
        current_biological_age=result["current_biological_age"],
        future_biological_age=result["future_biological_age"],
        organ_health=result["organ_health"],
        disease_progression=result["disease_progression"],
        ai_narrative=narrative,
        scenario=scenario,
    )


@router.post("/bioage-card")
async def biological_age_card(
    body: TimeMachineRequest,
    user: dict               = Depends(get_current_user),
    tm:   TimeMachineService = Depends(get_time_machine_service),
    groq: GroqService        = Depends(get_groq_service),
) -> dict:
    """
    Returns biological age data formatted for the Shock Card display.
    Computes the age gap, top causes of acceleration, and two 5-year
    trajectories (status-quo vs. with-prevention).
    """
    profile = body.current_profile.model_dump()
    profile["vitals"]["bmi"] = round(
        profile["vitals"]["weight"] / ((profile["vitals"]["height"] / 100) ** 2), 1
    )

    # Status-quo projection (1 year, used only to get current bio age)
    result_sq = tm.project(profile, 1, with_prevention=False)

    chrono_age = profile.get("age", 35)
    bio_age    = result_sq["current_biological_age"]
    gap        = bio_age - chrono_age

    # 5-year trajectories for comparison display
    result_5_sq  = tm.project(profile, 5, with_prevention=False)
    result_5_pv  = tm.project(profile, 5, with_prevention=True)

    # Identify top causes of biological age gap
    v   = profile.get("vitals", {})
    lif = profile.get("lifestyle", {})
    causes: list[str] = []
    if lif.get("smoking"):
        causes.append("smoking (adds ~5 biological years)")
    if lif.get("sleep_hours", 7) < 6:
        causes.append(f"sleep deficit ({lif.get('sleep_hours')}h nightly)")
    if lif.get("stress_level", 5) >= 7:
        causes.append(f"chronic stress (level {lif.get('stress_level')}/10)")
    if v.get("bmi", 25) > 27:
        causes.append(f"elevated BMI ({v.get('bmi',25):.1f})")
    if v.get("systolic_bp", 120) > 130:
        causes.append(f"elevated BP ({v.get('systolic_bp')}/{v.get('diastolic_bp')})")

    # AI narrative
    try:
        narrative = await groq.biological_age_narrative(
            chrono_age, bio_age, profile.get("name", "Patient"), causes[:3]
        )
    except Exception:
        if gap > 0:
            top2 = " and ".join(causes[:2]) if causes else "chronic stress and sleep deficit"
            narrative = (
                f"Your body is functioning like it's {bio_age}, not {chrono_age}. "
                f"The primary accelerators are {top2}. "
                "Addressing these consistently can recover 2–4 biological years within 90 days."
            )
        else:
            narrative = (
                f"Your biological age is {abs(gap)} years younger than your birth certificate. "
                "Your current habits — sleep, activity, and stress management — are actively protecting you. "
                "Keep them."
            )

    return {
        "chronological_age":      chrono_age,
        "biological_age":         bio_age,
        "gap":                    gap,
        "gap_direction":          "older" if gap > 0 else "younger",
        "top_causes":             causes[:3],
        "narrative":              narrative,
        "recovery_possible":      gap > 0,
        "status_quo_bio_age_5yr": result_5_sq["future_biological_age"],
        "prevention_bio_age_5yr": result_5_pv["future_biological_age"],
        "chrono_age_in_5yr":      chrono_age + 5,
    }
