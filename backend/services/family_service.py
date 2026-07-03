"""
MediTwin AI — Family Health Intelligence Service (MODULE 1)
═══════════════════════════════════════════════════════════════
Generational Health Twin: builds a multi-generation family graph,
computes hereditary risk multipliers from documented epidemiological
heredity factors, and produces data for the family tree + genetic
risk heatmap + inheritance-path visualizations.

Hereditary multiplier basis (population-level, documented ranges):
  • Diabetes (T2D): one first-degree relative affected → ~2x lifetime
    risk (ADA / CDC National Diabetes Statistics Report). Early-onset
    diagnosis (<50y) carries a stronger genetic signal → extra weight.
  • Hypertension: heritability estimates ~30-50% → one affected parent
    roughly 1.5-2x risk (Framingham Heart Study family data).
  • Heart Disease: family history of EARLY CVD (<55 male / <65 female)
    is itself a Framingham risk-score component → ~1.5-2x.
  • Anemia: largely nutritional in general population; hereditary forms
    (thalassemia trait etc.) flagged separately with high weight if
    explicitly recorded.

Multiplier formula (transparent, capped):
    multiplier = 1 + 0.5 * Σ(relative_weight)
    relative_weight = degree_weight * onset_weight
    degree_weight: first-degree = 1.0, second-degree = 0.4
    onset_weight:  early-onset (<50y) = 1.3, else = 1.0
    multiplier capped at 3.0x
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations
from typing import Any

from models.schemas import (
    ContributingRelative, FamilyMember, FamilyTreeNode,
    HereditaryRiskItem, HereditaryRiskResponse, InheritancePath,
)
from services.clinical_risk_service import get_clinical_risk_service

# Maps a disease name -> condition keywords that count as "this disease" in family history
_DISEASE_KEYWORDS: dict[str, list[str]] = {
    "Diabetes":        ["diabetes", "t2dm", "t1dm", "sugar"],
    "Heart Disease":   ["heart", "cardiac", "cvd", "myocardial", "stroke"],
    "Hypertension":    ["hypertension", "high bp", "blood pressure"],
    "Anemia":          ["anemia", "anaemia", "thalassemia", "thalassaemia"],
    "Stress Syndrome": ["anxiety", "depression", "stress", "burnout"],
}

# First-degree relations (parents, siblings, children)
_FIRST_DEGREE = {-1: True, 0: True, 1: True}  # generation -1 (parents), 0 (siblings), +1 (children)
# Note: generation 0 with id != "self" => sibling => first-degree


def _degree_weight(member: FamilyMember) -> float:
    """1.0 for first-degree relatives, 0.4 for second-degree (grandparents/aunts/uncles)."""
    if member.id == "self":
        return 0.0
    if member.generation in (-1, 1):          # parents / children
        return 1.0
    if member.generation == 0:                 # siblings
        return 1.0
    if member.generation == -2:                 # grandparents
        return 0.4
    return 0.3  # aunts/uncles or other extended relations


def _onset_weight(member: FamilyMember, condition: str) -> float:
    onset = member.age_at_diagnosis.get(condition)
    if onset is not None and onset < 50:
        return 1.3
    return 1.0


def _matches_disease(condition: str, disease: str) -> bool:
    c = condition.lower()
    return any(kw in c for kw in _DISEASE_KEYWORDS.get(disease, []))


def _risk_band(score: float) -> str:
    if score < 25:   return "low"
    if score < 50:   return "moderate"
    if score < 75:   return "high"
    return "critical"


class FamilyHealthService:

    def __init__(self) -> None:
        self.clinical = get_clinical_risk_service()

    # ── Hereditary risk computation ──────────────────────
    def compute_hereditary_risks(
        self, patient_profile: dict[str, Any], family_members: list[FamilyMember]
    ) -> list[HereditaryRiskItem]:
        base_risks = self.clinical.predict_all_risks(patient_profile)
        results: list[HereditaryRiskItem] = []

        for risk in base_risks:
            disease = risk.disease
            contributing: list[ContributingRelative] = []
            weight_sum = 0.0

            for member in family_members:
                if member.id == "self":
                    continue
                for condition in member.conditions:
                    if _matches_disease(condition, disease):
                        dw = _degree_weight(member)
                        ow = _onset_weight(member, condition)
                        w  = dw * ow
                        weight_sum += w
                        contributing.append(ContributingRelative(
                            relation=member.relation,
                            condition=condition,
                            age_at_diagnosis=member.age_at_diagnosis.get(condition),
                            weight=round(w, 2),
                        ))

            multiplier = round(min(3.0, 1.0 + 0.5 * weight_sum), 2)
            adjusted   = round(min(95.0, risk.probability * multiplier), 1)

            results.append(HereditaryRiskItem(
                disease=disease,
                base_risk=risk.probability,
                hereditary_multiplier=multiplier,
                adjusted_risk=adjusted,
                contributing_relatives=contributing,
            ))

        return results

    # ── Family tree for visualization ────────────────────
    def build_family_tree(
        self, patient_profile: dict[str, Any], family_members: list[FamilyMember]
    ) -> list[FamilyTreeNode]:
        nodes: list[FamilyTreeNode] = []

        # Self node — risk = patient's own average clinical risk
        base_risks = self.clinical.predict_all_risks(patient_profile)
        avg_risk = sum(r.probability for r in base_risks) / len(base_risks)
        nodes.append(FamilyTreeNode(
            id="self", relation="You", generation=0,
            name=patient_profile.get("name", "Patient"),
            age=patient_profile.get("age"), alive=True,
            conditions=patient_profile.get("medical_history", []),
            risk_score=round(avg_risk, 1), risk_band=_risk_band(avg_risk),
        ))

        # Family members — risk_score is a simple proxy: # of conditions * 20, capped
        for m in family_members:
            score = min(95.0, len(m.conditions) * 22.0)
            nodes.append(FamilyTreeNode(
                id=m.id, relation=m.relation, generation=m.generation,
                name=m.name or m.relation, age=m.age, alive=m.alive,
                conditions=m.conditions, risk_score=score, risk_band=_risk_band(score),
            ))

        return nodes

    # ── Inheritance paths ─────────────────────────────────
    def build_inheritance_paths(
        self, family_members: list[FamilyMember], hereditary_risks: list[HereditaryRiskItem]
    ) -> list[InheritancePath]:
        paths: list[InheritancePath] = []
        for hr in hereditary_risks:
            for rel in hr.contributing_relatives:
                paths.append(InheritancePath(
                    disease=hr.disease,
                    from_member=rel.relation,
                    to_member="Self",
                    strength=round(min(1.0, rel.weight), 2),
                ))
        return paths

    # ── Family-wide preventive actions ────────────────────
    def family_preventive_actions(
        self, hereditary_risks: list[HereditaryRiskItem]
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        elevated = [hr for hr in hereditary_risks if hr.hereditary_multiplier > 1.3]
        elevated.sort(key=lambda x: x.adjusted_risk, reverse=True)

        action_library = {
            "Diabetes": "Family-wide annual HbA1c screening; shared low-glycemic diet plan for the household",
            "Hypertension": "Household sodium-reduction (shared kitchen salt cap); BP monitor for shared home use",
            "Heart Disease": "Family cardiology screening from age 35 if any first-degree relative had early CVD",
            "Anemia": "Iron-rich diet plan for the household; screen all members with hemoglobin test",
            "Stress Syndrome": "Shared family wellness routine — group activity, consistent sleep schedule",
        }

        for hr in elevated[:4]:
            actions.append({
                "disease": hr.disease,
                "action": action_library.get(hr.disease, "Family screening recommended"),
                "adjusted_risk_pct": hr.adjusted_risk,
                "hereditary_multiplier": hr.hereditary_multiplier,
                "priority": "high" if hr.adjusted_risk > 50 else "medium",
            })
        return actions

    # ── Next-generation risk simulation ────────────────────
    def next_generation_risk(self, hereditary_risks: list[HereditaryRiskItem]) -> dict[str, float]:
        """
        Estimate the risk a HYPOTHETICAL child of the patient would inherit,
        assuming the patient's own (already hereditarily-adjusted) risk acts
        as the new generation's family-history input.
        Approximation: child_risk = adjusted_risk * 0.55 (one additional
        generation of dilution, consistent with the first-degree weight of 1.0
        in compute_hereditary_risks combined with the base multiplier formula).
        """
        return {
            hr.disease: round(min(95.0, hr.adjusted_risk * 0.55), 1)
            for hr in hereditary_risks
        }

    # ── Full pipeline ───────────────────────────────────────
    def generate_report(
        self, patient_profile: dict[str, Any], family_members: list[FamilyMember]
    ) -> tuple[list[HereditaryRiskItem], list[FamilyTreeNode], list[InheritancePath],
               list[dict[str, Any]], dict[str, float]]:
        hereditary = self.compute_hereditary_risks(patient_profile, family_members)
        tree       = self.build_family_tree(patient_profile, family_members)
        paths      = self.build_inheritance_paths(family_members, hereditary)
        actions    = self.family_preventive_actions(hereditary)
        next_gen   = self.next_generation_risk(hereditary)
        return hereditary, tree, paths, actions, next_gen


_instance: FamilyHealthService | None = None

def get_family_service() -> FamilyHealthService:
    global _instance
    if _instance is None:
        _instance = FamilyHealthService()
    return _instance
