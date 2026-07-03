"""MediTwin AI — Family Health Intelligence Router (MODULE 1)"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from models.schemas import FamilyHealthGraphRequest, HereditaryRiskResponse
from routers.auth import get_current_user
from services.family_service import FamilyHealthService, get_family_service
from services.groq_service import GroqService, get_groq_service

router = APIRouter()


@router.post("/hereditary-risk", response_model=HereditaryRiskResponse)
async def hereditary_risk(
    body: FamilyHealthGraphRequest,
    user:   dict              = Depends(get_current_user),
    family: FamilyHealthService = Depends(get_family_service),
    groq:   GroqService          = Depends(get_groq_service),
) -> HereditaryRiskResponse:
    """
    Builds the multi-generation family graph and computes hereditary
    risk multipliers, family tree visualization data, inheritance paths,
    family-wide preventive actions, and next-generation risk.
    """
    profile = body.patient.model_dump()
    profile["vitals"]["bmi"] = round(
        profile["vitals"]["weight"] / ((profile["vitals"]["height"] / 100) ** 2), 1
    )

    hereditary, tree, paths, actions, next_gen = family.generate_report(profile, body.family_members)

    # AI narrative summarizing the family risk picture
    top = sorted(hereditary, key=lambda x: x.adjusted_risk, reverse=True)[:2]
    summary_prompt = (
        f"Write a 3-sentence family health summary for {body.patient.name}. "
        f"Their hereditary-adjusted top risks are: "
        + ", ".join(f"{h.disease} {h.adjusted_risk}% (base {h.base_risk}%, "
                     f"family multiplier {h.hereditary_multiplier}x)" for h in top)
        + ". Mention which relatives contribute most and one family-wide preventive action. "
          "Empathetic, evidence-based, max 80 words."
    )
    try:
        ai_summary, _ = await groq.chat([{"role": "user", "content": summary_prompt}], max_tokens=180)
    except Exception:
        ai_summary = (
            f"{body.patient.name}'s family history meaningfully raises certain risks — "
            f"most notably {top[0].disease if top else 'overall metabolic'} risk, elevated by "
            f"{top[0].hereditary_multiplier if top else 1.0}x due to family history. "
            "A shared household preventive plan is recommended."
        )

    return HereditaryRiskResponse(
        patient_id=user.get("user_id", "anon"),
        hereditary_risks=hereditary,
        family_tree=tree,
        inheritance_paths=paths,
        family_preventive_actions=actions,
        next_generation_risk=next_gen,
        ai_summary=ai_summary,
    )
