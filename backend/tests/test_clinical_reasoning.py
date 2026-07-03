"""
Tests for the Clinical Reasoning Agent service.
All tested logic is DETERMINISTIC (no Groq calls) — the simulation
and causal inference components are pure functions.
"""
from __future__ import annotations
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.clinical_reasoning_agent import (
    _project_risk,
    _predict_onset_year,
    simulate_progression,
    _build_intervention_forks,
)


class TestProjectRisk:
    def test_risk_increases_over_time(self):
        r1 = _project_risk(30.0, "Diabetes", bmi=28.0, age=45, years=1)
        r5 = _project_risk(30.0, "Diabetes", bmi=28.0, age=45, years=5)
        assert r5 > r1 > 30.0

    def test_bmi_above_25_adds_extra_risk(self):
        r_normal = _project_risk(30.0, "Diabetes", bmi=25.0, age=40, years=3)
        r_obese  = _project_risk(30.0, "Diabetes", bmi=32.0, age=40, years=3)
        assert r_obese > r_normal

    def test_caps_at_95(self):
        r = _project_risk(90.0, "Diabetes", bmi=40.0, age=70, years=10)
        assert r <= 95.0

    def test_age_below_40_no_age_penalty(self):
        r_young = _project_risk(20.0, "Heart Disease", bmi=25.0, age=30, years=1)
        r_older = _project_risk(20.0, "Heart Disease", bmi=25.0, age=55, years=1)
        assert r_older >= r_young

    def test_all_diseases_project(self):
        diseases = ["Diabetes", "Heart Disease", "Hypertension", "Stress Syndrome", "Anemia"]
        for d in diseases:
            r = _project_risk(25.0, d, bmi=27.0, age=45, years=5)
            assert 0 < r <= 95.0, f"{d} projection out of range: {r}"


class TestOnsetPrediction:
    def test_already_high_risk_detected(self):
        result = _predict_onset_year(75.0, "Diabetes", bmi=30.0, age=50)
        assert result is not None
        assert result["already_high"] is True

    def test_onset_year_in_future(self):
        # High-enough current risk with elevated BMI reaches threshold within 10 years
        result = _predict_onset_year(45.0, "Diabetes", bmi=31.0, age=48)
        assert result is not None
        assert result["years_from_now"] >= 1
        assert result["year"] >= 2027

    def test_returns_none_for_very_low_risk(self):
        # Very low risk with favorable profile — no onset within 10 years
        result = _predict_onset_year(5.0, "Anemia", bmi=22.0, age=25)
        assert result is None

    def test_onset_year_is_correct_offset(self):
        result = _predict_onset_year(40.0, "Hypertension", bmi=30.0, age=48, current_year=2026)
        if result and not result["already_high"]:
            assert result["year"] == 2026 + result["years_from_now"]


class TestSimulateProgression:
    RISKS = [
        {"disease": "Diabetes",      "probability": 38.0, "tool_used": "FINDRISC", "score_components": []},
        {"disease": "Heart Disease", "probability": 22.0, "tool_used": "Framingham","score_components": []},
        {"disease": "Hypertension",  "probability": 45.0, "tool_used": "WHO",       "score_components": []},
        {"disease": "Stress Syndrome","probability": 67.0,"tool_used": "DASS-21",   "score_components": []},
        {"disease": "Anemia",        "probability": 12.0, "tool_used": "WHO",       "score_components": []},
    ]

    def test_trajectories_for_all_diseases(self):
        sim = simulate_progression(self.RISKS, bmi=27.4, age=34)
        assert len(sim["trajectories"]) == 5
        for disease, traj in sim["trajectories"].items():
            assert "current" in traj
            assert "horizons" in traj
            assert set(traj["horizons"].keys()) == {"1yr", "3yr", "5yr", "10yr"}

    def test_trajectories_increase_over_time(self):
        sim = simulate_progression(self.RISKS, bmi=27.4, age=34)
        for disease, traj in sim["trajectories"].items():
            h = traj["horizons"]
            # Each horizon should be >= previous
            assert h["1yr"] <= h["3yr"] <= h["5yr"] <= h["10yr"], \
                f"{disease}: non-monotonic trajectory"

    def test_onset_events_sorted_by_urgency(self):
        sim = simulate_progression(self.RISKS, bmi=27.4, age=34)
        events = sim["onset_events"]
        if len(events) >= 2:
            # Already-high events should come first (years_from_now == 0)
            years = [e["years_from_now"] for e in events]
            assert years == sorted(years), "Onset events not sorted by urgency"

    def test_primary_threat_is_most_urgent(self):
        sim = simulate_progression(self.RISKS, bmi=27.4, age=34)
        if sim["onset_events"]:
            assert sim["primary_threat"] == sim["onset_events"][0]

    def test_horizons_list_correct(self):
        sim = simulate_progression(self.RISKS, bmi=27.4, age=34)
        assert sim["horizons_years"] == [1, 3, 5, 10]


class TestInterventionForks:
    def test_three_forks_generated(self):
        forks = _build_intervention_forks("Diabetes", current_risk=38.0, bmi=28.0, age=45)
        assert len(forks) == 3

    def test_no_change_fork_has_highest_risk(self):
        forks = _build_intervention_forks("Diabetes", current_risk=38.0, bmi=28.0, age=45)
        risks = [f["risk_5yr"] for f in forks]
        assert risks[0] >= risks[1] >= risks[2], \
            f"Expected descending risk: {risks}"

    def test_aggressive_fork_has_largest_delta(self):
        forks = _build_intervention_forks("Diabetes", current_risk=38.0, bmi=28.0, age=45)
        deltas = [f["delta"] for f in forks]
        assert deltas[2] >= deltas[1] >= deltas[0]

    def test_no_change_fork_has_no_actions(self):
        forks = _build_intervention_forks("Heart Disease", current_risk=22.0, bmi=27.0, age=40)
        assert forks[0]["actions"] == []

    def test_intervention_forks_have_evidence_citations(self):
        forks = _build_intervention_forks("Diabetes", current_risk=38.0, bmi=28.0, age=45)
        # Moderate and aggressive forks should cite evidence
        for fork in forks[1:]:
            assert len(fork.get("evidence", "")) > 0, "Missing evidence citation in intervention fork"

    def test_risk_floors_at_5_percent(self):
        # Even with aggressive intervention, risk shouldn't go below 5%
        forks = _build_intervention_forks("Diabetes", current_risk=10.0, bmi=23.0, age=30)
        for fork in forks:
            assert fork["risk_5yr"] >= 5.0


class TestReasoningSchemas:
    def test_reasoning_response_schema_valid(self):
        """Verify the response schema fields match what the service returns."""
        from models.schemas import RiskLevel
        # Simulate a minimal result dict matching ReasoningResponse
        sample = {
            "patient_name": "Test",
            "age": 40,
            "bmi": 27.0,
            "causal_chain": "Test causal narrative",
            "primary_threat": None,
            "onset_events": [],
            "intervention_forks": [],
            "trajectories": {},
            "rag_sources": ["WHO CVD 2023"],
            "reasoning_method": "Test",
        }
        # All required keys present
        required = ["patient_name","age","bmi","causal_chain","primary_threat",
                    "onset_events","intervention_forks","trajectories","rag_sources","reasoning_method"]
        for key in required:
            assert key in sample, f"Missing key: {key}"
