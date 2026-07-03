"""
MediTwin AI — Preventive Impact Service (MODULE 3)
═══════════════════════════════════════════════════════════════
AI Preventive Impact Engine: quantifies PREVENTION instead of just
disease — converts lifestyle actions into risk-reduction percentages,
health-score gains, life-expectancy-year gains, and estimated
treatment-cost savings (₹).

Relative Risk Reduction (RRR) basis per action — published sources:
  • walk_10k   (10,000 steps/day, ~150 min/wk moderate activity):
        Diabetes RRR ~30% (Diabetes Prevention Program, NEJM 2002,
        lifestyle arm reduced T2D incidence ~58% with combined
        diet+activity+weight loss — 30% attributed to activity alone
        is a conservative sub-component estimate)
        Heart Disease RRR ~25% (meta-analyses of physical activity
        and CVD incidence, e.g. Sattelmair et al., Circulation 2011)
        Hypertension RRR ~20%
  • reduce_sugar (cut added sugar, low-glycemic diet):
        Diabetes RRR ~20%
  • reduce_sodium (DASH-aligned sodium reduction):
        Hypertension RRR ~25% (DASH-Sodium Trial, NEJM 2001 — SBP
        reduction of ~5-6 mmHg with sodium restriction)
        Heart Disease RRR ~10%
  • sleep_8h (consistent 7-8h sleep):
        Hypertension RRR ~15%
        Stress Syndrome RRR ~25%
  • quit_smoking:
        Heart Disease RRR ~50% (excess CVD risk declines substantially
        within 1 year of cessation — multiple cohort studies)
        Hypertension RRR ~10%
  • meditation (daily mindfulness/stress management):
        Stress Syndrome RRR ~35%
        Hypertension RRR ~10%
  • weight_loss (5-7% body weight reduction + sustained activity):
        Diabetes RRR ~45% (DPP combined lifestyle arm benchmark)
        Heart Disease RRR ~15%
        Hypertension RRR ~20%

Combined-action diminishing returns: when N actions are selected,
total effect = (sum of individual RRRs) * diminishing_factor(N), where
diminishing_factor = 1.0 (N=1), 0.90 (N=2), 0.80 (N=3), 0.72 (N=4+).
This avoids unrealistic "100% risk eliminated" outputs from stacking.

Life-expectancy gains (years) per action — conservative literature-
aligned point estimates, summed with the same diminishing-returns
factor and capped at +8.0 years total:
  walk_10k: +3.0   | quit_smoking: +3.0 | weight_loss: +2.0
  reduce_sodium: +1.0 | sleep_8h: +1.0 | reduce_sugar: +1.0 | meditation: +0.5
  (UK Biobank / Harvard Alumni Health Study style population estimates)

Cost-savings basis: ESTIMATED average lifetime treatment+management
cost in India IF the condition develops (medication, monitoring,
complication risk) — illustrative figures clearly labeled as
estimates for awareness purposes, not actuarial guarantees:
  Diabetes: ₹3,00,000 | Heart Disease: ₹5,00,000 | Hypertension: ₹1,50,000
  Anemia: ₹20,000 | Stress Syndrome: ₹50,000

savings_for_disease = (absolute_risk_reduction_pct_points / 100)
                       * avg_treatment_cost_if_diagnosed
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations
from typing import Any

from models.schemas import ActionDefinition, CostSavingItem, RiskReductionItem
from services.clinical_risk_service import get_clinical_risk_service


ACTION_LIBRARY: dict[str, dict[str, Any]] = {
    "sleep_8h": {
        "label": "Sleep 8 Hours/Night",
        "description": "Consistent 7-8h sleep schedule — reduces cortisol-driven BP and stress",
        "icon": "😴",
        "rrr": {"Hypertension": 0.15, "Stress Syndrome": 0.25},
        "life_years": 1.0,
    },
    "walk_10k": {
        "label": "Walk 10,000 Steps/Day",
        "description": "~150 min/week moderate activity — DPP-aligned metabolic + cardiac benefit",
        "icon": "🚶",
        "rrr": {"Diabetes": 0.30, "Heart Disease": 0.25, "Hypertension": 0.20},
        "life_years": 3.0,
    },
    "reduce_sugar": {
        "label": "Reduce Added Sugar",
        "description": "Low-glycemic diet shift — reduces fasting glucose trajectory",
        "icon": "🍬",
        "rrr": {"Diabetes": 0.20},
        "life_years": 1.0,
    },
    "reduce_sodium": {
        "label": "Reduce Sodium Intake",
        "description": "DASH-aligned sodium reduction — proven systolic BP reduction",
        "icon": "🧂",
        "rrr": {"Hypertension": 0.25, "Heart Disease": 0.10},
        "life_years": 1.0,
    },
    "quit_smoking": {
        "label": "Quit Smoking",
        "description": "Excess CVD risk declines substantially within 1 year of cessation",
        "icon": "🚭",
        "rrr": {"Heart Disease": 0.50, "Hypertension": 0.10},
        "life_years": 3.0,
    },
    "meditation": {
        "label": "Daily Meditation",
        "description": "10-min daily mindfulness — measurable cortisol and BP reduction",
        "icon": "🧘",
        "rrr": {"Stress Syndrome": 0.35, "Hypertension": 0.10},
        "life_years": 0.5,
    },
    "weight_loss": {
        "label": "5-7% Weight Loss",
        "description": "Sustained moderate weight loss — DPP headline metabolic benefit",
        "icon": "⚖️",
        "rrr": {"Diabetes": 0.45, "Heart Disease": 0.15, "Hypertension": 0.20},
        "life_years": 2.0,
    },
}

AVG_TREATMENT_COST_INR: dict[str, float] = {
    "Diabetes":        300_000,
    "Heart Disease":   500_000,
    "Hypertension":    150_000,
    "Anemia":           20_000,
    "Stress Syndrome":  50_000,
}

_DIMINISHING = {1: 1.00, 2: 0.90, 3: 0.80}
_DIMINISHING_DEFAULT = 0.72
_MAX_LIFE_GAIN_YEARS = 8.0


class PreventiveImpactService:

    def __init__(self) -> None:
        self.clinical = get_clinical_risk_service()

    def list_actions(self) -> list[ActionDefinition]:
        return [
            ActionDefinition(id=aid, label=a["label"], description=a["description"], icon=a["icon"])
            for aid, a in ACTION_LIBRARY.items()
        ]

    def compute_impact(self, profile: dict[str, Any], action_ids: list[str]) -> dict[str, Any]:
        valid_actions = [a for a in action_ids if a in ACTION_LIBRARY]
        n = max(1, len(valid_actions))
        diminish = _DIMINISHING.get(n, _DIMINISHING_DEFAULT)

        before_risks = {r.disease: r.probability for r in self.clinical.predict_all_risks(profile)}

        # Aggregate RRR per disease across selected actions (sum, then apply diminishing factor)
        aggregate_rrr: dict[str, float] = {}
        for aid in valid_actions:
            for disease, rrr in ACTION_LIBRARY[aid]["rrr"].items():
                aggregate_rrr[disease] = aggregate_rrr.get(disease, 0.0) + rrr

        risk_reductions: list[RiskReductionItem] = []
        cost_breakdown:  list[CostSavingItem] = []
        total_savings = 0.0

        for disease, before in before_risks.items():
            rrr_total = min(0.85, aggregate_rrr.get(disease, 0.0) * diminish)  # cap RRR at 85%
            after = round(max(2.0, before * (1 - rrr_total)), 1)
            abs_reduction = round(before - after, 1)

            risk_reductions.append(RiskReductionItem(
                disease=disease, before_pct=before, after_pct=after,
                reduction_pct=abs_reduction, relative_reduction_pct=round(rrr_total * 100, 1),
            ))

            if abs_reduction > 0:
                avg_cost = AVG_TREATMENT_COST_INR.get(disease, 0)
                savings  = round((abs_reduction / 100) * avg_cost, 0)
                total_savings += savings
                cost_breakdown.append(CostSavingItem(
                    disease=disease, avoided_risk_points=abs_reduction,
                    avg_treatment_cost_inr=avg_cost, estimated_savings_inr=savings,
                    basis=f"{abs_reduction}% risk reduction × ₹{avg_cost:,.0f} avg. treatment cost",
                ))

        # Life expectancy gain
        raw_life_gain = sum(ACTION_LIBRARY[aid]["life_years"] for aid in valid_actions) * diminish
        life_gain = round(min(_MAX_LIFE_GAIN_YEARS, raw_life_gain), 1)

        # Health score impact — build a "future profile" with RRR applied to underlying drivers
        # (simplified: scale health score increase proportionally to avg risk reduction)
        avg_reduction_pct_points = (
            sum(r.reduction_pct for r in risk_reductions) / len(risk_reductions)
            if risk_reductions else 0.0
        )
        before_score = self.clinical.compute_health_score(profile)
        score_increase = int(round(avg_reduction_pct_points * 0.6))
        after_score = max(before_score, min(100, before_score + score_increase))

        return {
            "selected_actions": valid_actions,
            "health_score_before": before_score,
            "health_score_after":  after_score,
            "health_score_increase": after_score - before_score,
            "risk_reductions": risk_reductions,
            "life_expectancy_gain_years": life_gain,
            "cost_savings_breakdown": cost_breakdown,
            "total_cost_savings_inr": total_savings,
            "assumptions": [
                f"{n} action(s) selected — combined effect scaled by diminishing-returns factor {diminish}",
                "RRR (Relative Risk Reduction) values derived from published intervention studies "
                "(DPP 2002, DASH-Sodium NEJM 2001, smoking-cessation cohort data, activity-CVD meta-analyses)",
                "Treatment cost estimates are illustrative averages for India and intended for "
                "awareness/education, not individual financial guarantees",
                f"Life expectancy gain capped at {_MAX_LIFE_GAIN_YEARS} years total",
            ],
        }


_instance: PreventiveImpactService | None = None

def get_preventive_impact_service() -> PreventiveImpactService:
    global _instance
    if _instance is None:
        _instance = PreventiveImpactService()
    return _instance
