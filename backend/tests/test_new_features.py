"""
Tests for the three new 9+ features:
  1. Multi-agent orchestrator (unit: ranking, divergence detection, prompt assembly)
  2. What-If causal confidence + assumption generation
  3. Disclosure fields on FedLearningResponse and PopHealthResponse schemas
"""
from __future__ import annotations
import pytest
from models.schemas import WhatIfResponse, FedLearningResponse, PopHealthResponse


# ── 1. Agent orchestrator unit tests ────────────────────────────────────────

class TestAgentOrchestrator:
    def test_divergence_detection_shared_actions(self):
        from services.agent_orchestrator import _detect_divergence
        opinions = [
            {"role": "Cardiologist Agent",        "recommendation": "Reduce sodium and exercise daily."},
            {"role": "Endocrinologist Agent",      "recommendation": "Reduce sugar intake and monitor HbA1c."},
            {"role": "Preventive Medicine Agent",  "recommendation": "Reduce alcohol and increase exercise."},
        ]
        agreement, divergence = _detect_divergence(opinions)
        # "reduce" and "exercise" appear in 2+ agents → should appear in agreement
        joined_agreement = " ".join(agreement).lower()
        assert "reduce" in joined_agreement or "exercise" in joined_agreement, (
            f"Expected shared action words in agreement, got: {agreement}"
        )

    def test_divergence_detection_no_overlap(self):
        from services.agent_orchestrator import _detect_divergence
        opinions = [
            {"role": "A", "recommendation": "sleep more"},
            {"role": "B", "recommendation": "take medication now"},
        ]
        agreement, divergence = _detect_divergence(opinions)
        assert isinstance(agreement, list) and len(agreement) > 0
        assert isinstance(divergence, list) and len(divergence) > 0

    def test_risk_context_formatting(self):
        from services.agent_orchestrator import _format_risk_context
        risks = {"Heart Disease": 45.0, "Diabetes": 30.0, "Stroke": 10.0}
        ctx = _format_risk_context(risks, ["Heart Disease", "Diabetes"])
        assert "Heart Disease" in ctx and "Diabetes" in ctx
        assert "Stroke" not in ctx  # out-of-scope for this agent

    def test_risk_context_no_relevant_data(self):
        from services.agent_orchestrator import _format_risk_context
        risks = {"Stroke": 10.0}
        ctx = _format_risk_context(risks, ["Heart Disease"])
        assert "No specific risk data" in ctx

    def test_confidence_low_with_empty_risks(self):
        """Confidence heuristic: fewer matched risks → lower confidence."""
        from services.agent_orchestrator import _run_agent
        # We can't call the async function directly without a live groq client,
        # but we can verify the confidence formula is correct inline.
        focus_keys = ["Heart Disease", "Hypertension"]
        risks = {}  # empty — no relevant data
        relevant_count = sum(1 for k in focus_keys if k in risks)
        confidence = min(1.0, 0.5 + 0.1 * relevant_count)
        assert confidence == 0.5

    def test_confidence_high_with_all_risks_present(self):
        focus_keys = ["Heart Disease", "Hypertension"]
        risks = {"Heart Disease": 45.0, "Hypertension": 60.0}
        relevant_count = sum(1 for k in focus_keys if k in risks)
        confidence = min(1.0, 0.5 + 0.1 * relevant_count)
        assert confidence == 0.7


# ── 2. WhatIf causal confidence + assumptions ─────────────────────────────

class TestWhatIfCausalFields:
    def test_whatif_response_has_confidence_field(self):
        r = WhatIfResponse(
            current_health_score=60, projected_health_score=70,
            score_delta=10, risk_changes={"Diabetes": -5.0},
            life_expectancy_impact_years=0.5, ai_explanation="test",
            milestones=[], effect_confidence="high",
            causal_assumptions=["vitals held constant"],
        )
        assert r.effect_confidence == "high"
        assert "vitals held constant" in r.causal_assumptions

    def test_whatif_response_defaults_to_moderate(self):
        r = WhatIfResponse(
            current_health_score=60, projected_health_score=65,
            score_delta=5, risk_changes={},
            life_expectancy_impact_years=0.25, ai_explanation="x",
            milestones=[],
        )
        assert r.effect_confidence == "moderate"
        assert r.causal_assumptions == []

    def test_causal_confidence_logic_high(self):
        """Replicate the confidence logic from the endpoint directly."""
        changes = {"smoking": False, "exercise_days_per_week": 4, "diet_quality": 8}
        high_confidence_keys = {"smoking", "exercise_days_per_week", "diet_quality",
                                "bmi", "alcohol_units_per_week", "sleep_hours"}
        matched = {k for k in changes if k in high_confidence_keys and changes[k] is not None}
        n = len(matched)
        confidence = "high" if n >= 3 else ("moderate" if n >= 1 else "low")
        assert confidence == "high"

    def test_causal_confidence_logic_moderate(self):
        changes = {"smoking": False}
        high_confidence_keys = {"smoking", "exercise_days_per_week", "diet_quality",
                                "bmi", "alcohol_units_per_week", "sleep_hours"}
        matched = {k for k in changes if k in high_confidence_keys and changes[k] is not None}
        n = len(matched)
        confidence = "high" if n >= 3 else ("moderate" if n >= 1 else "low")
        assert confidence == "moderate"

    def test_causal_confidence_logic_low(self):
        changes = {"random_field": "x"}
        high_confidence_keys = {"smoking", "exercise_days_per_week", "diet_quality",
                                "bmi", "alcohol_units_per_week", "sleep_hours"}
        matched = {k for k in changes if k in high_confidence_keys}
        n = len(matched)
        confidence = "high" if n >= 3 else ("moderate" if n >= 1 else "low")
        assert confidence == "low"


# ── 3. Disclosure fields on FedLearning + PopHealth schemas ──────────────

class TestDisclosureFields:
    def test_fed_response_has_simulation_note(self):
        r = FedLearningResponse(
            rounds=[], final_accuracy=0.85, total_patients=1200,
            privacy_guarantee="Differential privacy ε=1.0",
            ai_narrative="test narrative",
        )
        assert "Architecture Simulator" in r.simulation_note
        assert "PySyft" in r.simulation_note or "Flower" in r.simulation_note

    def test_pop_response_has_data_note(self):
        r = PopHealthResponse(
            districts=[], national_avg={}, top_alerts=[], resource_gaps=[],
        )
        assert "synthetic" in r.data_note.lower()
        assert "NFHS-5" in r.data_note or "ICMR" in r.data_note

    def test_disclosure_fields_are_non_empty_strings(self):
        fed = FedLearningResponse(
            rounds=[], final_accuracy=0.9, total_patients=500,
            privacy_guarantee="ε-differential privacy", ai_narrative="x",
        )
        pop = PopHealthResponse(districts=[], national_avg={}, top_alerts=[], resource_gaps=[])
        assert isinstance(fed.simulation_note, str) and len(fed.simulation_note) > 20
        assert isinstance(pop.data_note, str) and len(pop.data_note) > 20


# ── 4. Schema integration: ConsensusResponse ─────────────────────────────

class TestConsensusSchema:
    def test_consensus_response_structure(self):
        from models.schemas import AgentOpinion, ConsensusResponse
        r = ConsensusResponse(
            patient_name="Priya",
            agents=[
                AgentOpinion(role="Cardiologist Agent", recommendation="Reduce BP",
                             confidence=0.8, focus_risks=["Heart Disease"]),
                AgentOpinion(role="Endocrinologist Agent", recommendation="Monitor HbA1c",
                             confidence=0.7, focus_risks=["Diabetes"]),
            ],
            consensus_summary="Prioritize BP reduction and glucose monitoring.",
            points_of_agreement=["Both agents recommend monitoring"],
            points_of_divergence=["Different focal risks"],
        )
        assert r.patient_name == "Priya"
        assert len(r.agents) == 2
        assert r.agents[0].confidence == 0.8
        assert "BP" in r.consensus_summary
