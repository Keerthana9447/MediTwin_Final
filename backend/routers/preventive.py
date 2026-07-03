"""MediTwin AI — Preventive Impact Engine Router (MODULE 3)"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from models.schemas import (
    ActionDefinition, PreventiveActionInput, PreventiveImpactResponse,
)
from routers.auth import get_current_user
from services.groq_service import GroqService, get_groq_service
from services.preventive_impact_service import (
    ACTION_LIBRARY, PreventiveImpactService, get_preventive_impact_service,
)

router = APIRouter()


@router.get("/actions", response_model=list[ActionDefinition])
async def list_actions(
    user: dict                    = Depends(get_current_user),
    svc:  PreventiveImpactService = Depends(get_preventive_impact_service),
) -> list[ActionDefinition]:
    """Returns the catalog of preventive actions the user can toggle."""
    return svc.list_actions()


@router.post("/impact", response_model=PreventiveImpactResponse)
async def compute_impact(
    body: PreventiveActionInput,
    user: dict                    = Depends(get_current_user),
    svc:  PreventiveImpactService = Depends(get_preventive_impact_service),
    groq: GroqService              = Depends(get_groq_service),
) -> PreventiveImpactResponse:
    """
    Computes risk-reduction %, health-score gain, life-expectancy gain,
    and estimated treatment-cost savings (₹) for the selected actions.
    """
    profile = body.current_profile.model_dump()
    profile["vitals"]["bmi"] = round(
        profile["vitals"]["weight"] / ((profile["vitals"]["height"] / 100) ** 2), 1
    )

    result = svc.compute_impact(profile, body.action_ids)

    action_labels = [
        ACTION_LIBRARY[a]["label"] for a in result["selected_actions"] if a in ACTION_LIBRARY
    ]

    if action_labels:
        prompt = (
            f"MediTwin Preventive Impact — {body.current_profile.name} selected: "
            f"{', '.join(action_labels)}. "
            f"Result: health score {result['health_score_before']} -> {result['health_score_after']}, "
            f"life expectancy +{result['life_expectancy_gain_years']} years, "
            f"estimated savings ₹{result['total_cost_savings_inr']:,.0f}. "
            "Write 2 motivating sentences, max 60 words, citing the most impactful change."
        )
        try:
            narrative, _ = await groq.chat([{"role": "user", "content": prompt}], max_tokens=140)
        except Exception:
            narrative = (
                f"These {len(action_labels)} change(s) could raise your health score by "
                f"{result['health_score_increase']} points, add roughly "
                f"{result['life_expectancy_gain_years']} years to your life expectancy, and avoid "
                f"an estimated ₹{result['total_cost_savings_inr']:,.0f} in future treatment costs."
            )
    else:
        narrative = "Select one or more preventive actions to see your personalized impact."

    return PreventiveImpactResponse(
        patient_id=user.get("user_id", "anon"),
        selected_actions=result["selected_actions"],
        health_score_before=result["health_score_before"],
        health_score_after=result["health_score_after"],
        health_score_increase=result["health_score_increase"],
        risk_reductions=result["risk_reductions"],
        life_expectancy_gain_years=result["life_expectancy_gain_years"],
        cost_savings_breakdown=result["cost_savings_breakdown"],
        total_cost_savings_inr=result["total_cost_savings_inr"],
        ai_narrative=narrative,
        assumptions=result["assumptions"],
    )
