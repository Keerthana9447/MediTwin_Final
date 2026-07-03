"""
MediTwin AI — Multi-Agent Specialist Consensus Router
POST /api/v1/consensus/analyze

Accepts the same PatientProfile used by /health-twin, fans out to
three specialist agents (Cardiologist, Endocrinologist, Preventive
Medicine) concurrently, and returns individual opinions + consensus
with explicit agreement/divergence detection.
"""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends

from models.schemas import (
    PatientProfile, AgentOpinion, ConsensusResponse,
)
from routers.auth import get_current_user
from services.groq_service import GroqService, get_groq_service
from services.clinical_risk_service import ClinicalRiskService, get_clinical_risk_service
from services.agent_orchestrator import run_consensus

router = APIRouter()


@router.post("/analyze", response_model=ConsensusResponse)
async def consensus_analyze(
    body:     PatientProfile,
    user:     dict                = Depends(get_current_user),
    groq:     GroqService         = Depends(get_groq_service),
    clinical: ClinicalRiskService = Depends(get_clinical_risk_service),
) -> ConsensusResponse:
    """
    Multi-agent specialist consensus analysis.

    1. Runs clinical_risk_service on the patient profile (same engine
       as /health-twin — so risk numbers are identical and auditable).
    2. Fans out CONCURRENTLY to 3 role-scoped specialist agents, each
       receiving only the risk data in their domain.
    3. Returns individual agent opinions + divergence-detected consensus.
    """
    profile: dict[str, Any] = body.model_dump()

    # Ensure BMI computed
    v = profile.get("vitals", {})
    if v.get("height") and v.get("weight") and not v.get("bmi"):
        v["bmi"] = round(v["weight"] / ((v["height"] / 100) ** 2), 1)
        profile["vitals"] = v

    # Get risks from the same engine /health-twin uses
    risk_results = clinical.predict_all_risks(profile)
    risks_dict: dict[str, float] = {r.disease: r.probability for r in risk_results}

    name = profile.get("name", "Patient")
    age  = profile.get("age", 35)

    result = await run_consensus(groq, name, age, risks_dict)

    return ConsensusResponse(
        patient_name=name,
        agents=[
            AgentOpinion(
                role=op["role"],
                recommendation=op["recommendation"],
                confidence=op["confidence"],
                focus_risks=op["focus_risks"],
            )
            for op in result["agents"]
        ],
        consensus_summary=result["consensus_summary"],
        points_of_agreement=result["points_of_agreement"],
        points_of_divergence=result["points_of_divergence"],
    )
