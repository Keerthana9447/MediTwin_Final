"""
MediTwin AI — Clinical Reasoning Agent Router
POST /api/v1/reasoning/analyze

The flagship GenAI endpoint for InnovaHack:
Takes a patient profile → runs multi-year disease simulation →
generates a causal chain narrative grounded in real guidelines.
"""
from __future__ import annotations
import os
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from routers.auth import get_current_user
from services.groq_service import GroqService, get_groq_service
from services.rag_service import RAGService, get_rag_service
from services.clinical_risk_service import ClinicalRiskService, get_clinical_risk_service
from services.clinical_reasoning_agent import run_clinical_reasoning

router = APIRouter()


class ReasoningRequest(BaseModel):
    name:      str   = "Patient"
    age:       int   = 40
    gender:    str   = "Male"
    vitals:    dict[str, Any] = {}
    lifestyle: dict[str, Any] = {}
    history:   list[str] = []


class InterventionFork(BaseModel):
    label:       str
    description: str
    risk_5yr:    float
    delta:       float
    actions:     list[str]
    evidence:    str = ""
    narrative:   str = ""


class OnsetEvent(BaseModel):
    disease:        str
    onset_year:     int
    years_from_now: int
    current_risk:   float
    projected_risk: float
    already_high:   bool
    source:         str = ""


class ReasoningResponse(BaseModel):
    patient_name:         str
    age:                  int
    bmi:                  float
    causal_chain:         str            # the LLM-generated narrative
    primary_threat:       OnsetEvent | None
    onset_events:         list[OnsetEvent]
    intervention_forks:   list[InterventionFork]
    trajectories:         dict[str, Any]  # disease → {current, horizons}
    rag_sources:          list[str]
    reasoning_method:     str


@router.post("/analyze", response_model=ReasoningResponse)
async def analyze(
    body:     ReasoningRequest,
    user:     dict                = Depends(get_current_user),
    groq:     GroqService         = Depends(get_groq_service),
    rag:      RAGService          = Depends(get_rag_service),
    clinical: ClinicalRiskService = Depends(get_clinical_risk_service),
) -> ReasoningResponse:
    """
    Clinical Reasoning Agent — flagship endpoint.

    Pipeline:
    1. Score all 5 diseases via validated clinical formulas (FINDRISC/Framingham/WHO)
    2. Simulate 10-year progression using published natural-history rates
    3. Predict first onset event with year estimate
    4. Generate 3 intervention forks with evidence citations
    5. Retrieve 2 relevant guideline chunks via RAG (TF-IDF over WHO/ICMR/ACC-AHA)
    6. Generate causal chain narrative via Groq — narrating simulation results,
       NOT guessing risk numbers from parametric LLM knowledge
    """
    profile: dict[str, Any] = body.model_dump()

    # Ensure BMI computed
    v = profile.get("vitals", {})
    if v.get("height") and v.get("weight") and not v.get("bmi"):
        v["bmi"] = round(v["weight"] / ((v["height"] / 100) ** 2), 1)
        profile["vitals"] = v

    bmi = float(v.get("bmi", 25.0))

    # Step 1: Score all risks
    risk_results = clinical.predict_all_risks(profile)
    risks_for_sim = [
        {
            "disease":          r.disease,
            "probability":      r.probability,
            "tool_used":        r.tool_used,
            "score_components": [{"factor": c.factor, "points": c.points} for c in r.score_components],
        }
        for r in risk_results
    ]

    # Profile summary for LLM context
    ls = profile.get("lifestyle", {})
    profile_summary = (
        f"BMI {bmi:.1f}, gender {body.gender}. "
        f"Smoking: {ls.get('smoking', False)}. "
        f"Exercise: {ls.get('exercise_days_per_week', 0)} days/week. "
        f"Sleep: {ls.get('sleep_hours', 7)} hours/night. "
        f"History: {', '.join(body.history) if body.history else 'None reported'}."
    )

    # Step 2-6: Full reasoning pipeline
    try:
        result = await run_clinical_reasoning(
            groq_service=groq,
            rag_service=rag,
            patient_name=body.name,
            age=body.age,
            bmi=bmi,
            risks=risks_for_sim,
            profile_summary=profile_summary,
        )
    except RuntimeError as exc:
        msg = str(exc)
        if "authentication" in msg.lower() or "api_key" in msg.lower() or "401" in msg:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=502,
                detail=(
                    "Groq API authentication failed. "
                    "Please check GROQ_API_KEY in your backend/.env file and restart the server. "
                    f"(Model: {os.getenv('GROQ_MODEL','openai/gpt-oss-120b')})"
                )
            )
        raise

    # Build typed onset events
    onset_events = [
        OnsetEvent(
            disease=e["disease"],
            onset_year=e["onset_year"],
            years_from_now=e["years_from_now"],
            current_risk=e["current_risk"],
            projected_risk=e["projected_risk"],
            already_high=e["already_high"],
            source=e.get("source", ""),
        )
        for e in result["simulation"]["onset_events"]
    ]

    primary_raw = result["simulation"]["primary_threat"]
    primary = OnsetEvent(**{
        "disease":        primary_raw["disease"],
        "onset_year":     primary_raw["onset_year"],
        "years_from_now": primary_raw["years_from_now"],
        "current_risk":   primary_raw["current_risk"],
        "projected_risk": primary_raw["projected_risk"],
        "already_high":   primary_raw["already_high"],
        "source":         primary_raw.get("source", ""),
    }) if primary_raw else None

    forks = [
        InterventionFork(
            label=f["label"],
            description=f["description"],
            risk_5yr=f["risk_5yr"],
            delta=f["delta"],
            actions=f["actions"],
            evidence=f.get("evidence", ""),
            narrative=f.get("narrative", ""),
        )
        for f in result["intervention_forks"]
    ]

    return ReasoningResponse(
        patient_name=result["patient_name"],
        age=result["age"],
        bmi=result["bmi"],
        causal_chain=result["causal_chain"],
        primary_threat=primary,
        onset_events=onset_events,
        intervention_forks=forks,
        trajectories=result["simulation"]["trajectories"],
        rag_sources=result["rag_sources"],
        reasoning_method=result["reasoning_method"],
    )
