"""
MediTwin AI — Health Time Machine Service (MODULE 2)
═══════════════════════════════════════════════════════════════
Future Self Engine: projects health 1/5/10 years forward using
documented age-risk progression rates and lifestyle-decay modifiers.

Progression-rate basis (per-decade absolute risk increase, applied
proportionally per year, documented ranges):
  • Heart Disease: 10-yr CVD risk roughly DOUBLES per decade after
    age 40 in Framingham cohort data when risk factors persist
    → modeled as +0.10 * current_risk per year (compounding).
  • Hypertension: prevalence rises ~5-8 percentage points per decade
    with sedentary lifestyle (NHANES-pattern population trends)
    → +0.6-0.8 pct-points/year baseline, modified by lifestyle.
  • Diabetes (FINDRISC-banded): age moves the FINDRISC age-band
    upward over time (e.g. <45 → 45-54 → 55-64), recomputed directly
    by re-running FINDRISC at the future age + projected BMI/glucose.
  • Anemia / Stress: largely lifestyle-driven; projected via lifestyle
    trajectory rather than age alone.

Biological age formula (transparent, capped at ±15 years):
    bio_delta =   0.3 * (BMI - 22)
                + 0.05 * max(0, systolic_bp - 120)
                + 0.05 * max(0, glucose - 90)
                + 0.8  * max(0, 7 - sleep_hours)
                + 0.5  * max(0, stress_level - 5)
                + (5 if smoking else 0)
    biological_age = chronological_age + bio_delta  (capped ±15)

Lifestyle-decay (status-quo trajectory, applied per projected year):
    BMI drift:      +0.15 kg/m² / year if exercise_days < 3
    SBP drift:      +0.8 mmHg / year if stress >= 7 or sleep < 6
    Glucose drift:  +1.2 mg/dL / year if diet_quality < 6
These are conservative population-trend approximations, NOT individual
medical predictions — clearly labeled in the AI narrative.

"with_prevention" scenario (Future B) zeroes out the lifestyle-decay
drift terms — i.e. assumes the patient SUSTAINS the improved habits
selected in the Preventive Impact Engine (Module 3).
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations
import copy
from typing import Any

from models.schemas import DiseaseProgression, OrganHealth
from services.clinical_risk_service import get_clinical_risk_service


# ── Organ health composite formulas ─────────────────────────
def _organ_scores(profile: dict[str, Any], risks: dict[str, float]) -> dict[str, int]:
    v, lif = profile.get("vitals", {}), profile.get("lifestyle", {})
    heart   = 100 - (risks.get("Heart Disease", 0) * 0.6 + risks.get("Hypertension", 0) * 0.4)
    pancreas= 100 - risks.get("Diabetes", 0)
    kidneys = 100 - (risks.get("Hypertension", 0) * 0.5 + risks.get("Diabetes", 0) * 0.3)
    lungs   = 100 - (15 if lif.get("smoking", False) else 0) - max(0, (profile.get("age", 35) - 40) * 0.3)
    brain   = 100 - (risks.get("Stress Syndrome", 0) * 0.6 + max(0, (7 - lif.get("sleep_hours", 7)) * 4))
    return {
        "Heart":    int(max(10, min(100, round(heart)))),
        "Pancreas": int(max(10, min(100, round(pancreas)))),
        "Kidneys":  int(max(10, min(100, round(kidneys)))),
        "Lungs":    int(max(10, min(100, round(lungs)))),
        "Brain":    int(max(10, min(100, round(brain)))),
    }


def _biological_age(profile: dict[str, Any]) -> int:
    v, lif = profile.get("vitals", {}), profile.get("lifestyle", {})
    age = profile.get("age", 35)
    bmi = v.get("bmi", 25.0)
    sbp = v.get("systolic_bp", 120)
    glu = v.get("glucose", 90)
    sleep = lif.get("sleep_hours", 7)
    stress = lif.get("stress_level", 5)
    smoking = lif.get("smoking", False)

    delta = (
        0.3 * (bmi - 22)
        + 0.05 * max(0, sbp - 120)
        + 0.05 * max(0, glu - 90)
        + 0.8 * max(0, 7 - sleep)
        + 0.5 * max(0, stress - 5)
        + (5 if smoking else 0)
    )
    delta = max(-15, min(15, delta))
    return int(round(age + delta))


class TimeMachineService:

    def __init__(self) -> None:
        self.clinical = get_clinical_risk_service()

    def _project_profile(self, profile: dict[str, Any], years: int, with_prevention: bool) -> dict[str, Any]:
        """Return a deep-copied profile representing the patient `years` from now."""
        proj = copy.deepcopy(profile)
        v, lif = proj.get("vitals", {}), proj.get("lifestyle", {})

        proj["age"] = profile.get("age", 35) + years

        if with_prevention:
            # Sustained improved habits → vitals trend toward healthy targets, no decay
            v["bmi"]         = max(21.0, v.get("bmi", 25.0) - 0.3 * years)
            v["systolic_bp"] = max(112, v.get("systolic_bp", 120) - 0.6 * years)
            v["glucose"]     = max(82, v.get("glucose", 90) - 0.8 * years)
            lif["sleep_hours"]   = min(8.0, lif.get("sleep_hours", 7) + 0.15 * years)
            lif["stress_level"]  = max(3, lif.get("stress_level", 5) - 0.3 * years)
            lif["exercise_days_per_week"] = min(6, lif.get("exercise_days_per_week", 3) + 0.3 * years)
        else:
            # Status-quo lifestyle-decay drift
            bmi_drift = 0.15 if lif.get("exercise_days_per_week", 3) < 3 else 0.03
            sbp_drift = 0.8 if (lif.get("stress_level", 5) >= 7 or lif.get("sleep_hours", 7) < 6) else 0.3
            glu_drift = 1.2 if lif.get("diet_quality", 6) < 6 else 0.4

            v["bmi"]         = v.get("bmi", 25.0) + bmi_drift * years
            v["systolic_bp"] = v.get("systolic_bp", 120) + sbp_drift * years
            v["glucose"]     = v.get("glucose", 90) + glu_drift * years

        proj["vitals"]    = v
        proj["lifestyle"] = lif
        return proj

    def project(
        self, profile: dict[str, Any], years: int, with_prevention: bool = False
    ) -> dict[str, Any]:
        current_risks  = {r.disease: r.probability for r in self.clinical.predict_all_risks(profile)}
        future_profile = self._project_profile(profile, years, with_prevention)
        future_risks_raw = self.clinical.predict_all_risks(future_profile)
        future_risks   = {r.disease: r.probability for r in future_risks_raw}

        disease_progression = [
            DiseaseProgression(
                disease=d,
                current_risk=current_risks.get(d, 0.0),
                future_risk=future_risks.get(d, 0.0),
                delta=round(future_risks.get(d, 0.0) - current_risks.get(d, 0.0), 1),
                tool_used=next((r.tool_used for r in future_risks_raw if r.disease == d), ""),
            )
            for d in current_risks
        ]

        current_organs = _organ_scores(profile, current_risks)
        future_organs  = _organ_scores(future_profile, future_risks)
        organ_health = [
            OrganHealth(organ=o, current_pct=current_organs[o], future_pct=future_organs[o],
                       delta=future_organs[o] - current_organs[o])
            for o in current_organs
        ]

        return {
            "current_age":            profile.get("age", 35),
            "future_age":             profile.get("age", 35) + years,
            "current_health_score":   self.clinical.compute_health_score(profile),
            "future_health_score":    self.clinical.compute_health_score(future_profile),
            "current_biological_age": _biological_age(profile),
            "future_biological_age":  _biological_age(future_profile),
            "organ_health":           organ_health,
            "disease_progression":    disease_progression,
            "future_profile":         future_profile,
        }

    def project_yearly_trajectory(
        self,
        profile: dict[str, Any],
        years: int,
        with_prevention: bool = False
    ) -> list[dict[str, Any]]:
        """
        Returns a data point for EACH year (not just the endpoint).
        Used by the Parallel Universe Simulator to draw continuous risk curves
        across multiple simultaneous timelines.
        """
        trajectory: list[dict[str, Any]] = []
        for y in range(0, years + 1):
            if y == 0:
                risks = {r.disease: r.probability for r in self.clinical.predict_all_risks(profile)}
                trajectory.append({
                    "year": y,
                    "age": profile.get("age", 35),
                    "health_score": self.clinical.compute_health_score(profile),
                    "risks": risks,
                    "biological_age": _biological_age(profile),
                })
            else:
                p = self._project_profile(profile, y, with_prevention)
                risks = {r.disease: r.probability for r in self.clinical.predict_all_risks(p)}
                trajectory.append({
                    "year": y,
                    "age": profile.get("age", 35) + y,
                    "health_score": self.clinical.compute_health_score(p),
                    "risks": risks,
                    "biological_age": _biological_age(p),
                })
        return trajectory


_instance: TimeMachineService | None = None

def get_time_machine_service() -> TimeMachineService:
    global _instance
    if _instance is None:
        _instance = TimeMachineService()
    return _instance
