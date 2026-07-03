"""
MediTwin AI — Pydantic v2 Schemas
No external email-validator dependency — uses plain str for email fields.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW      = "low"
    MODERATE = "moderate"
    HIGH     = "high"
    CRITICAL = "critical"

class TriageLevel(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"

class Gender(str, Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"


# ── Auth ─────────────────────────────────────────────────
class UserRegister(BaseModel):
    name:     str = Field(..., min_length=2, max_length=100)
    email:    str = Field(..., description="User email address")
    password: str = Field(..., min_length=8)
    role:     str = Field(default="patient")

class UserLogin(BaseModel):
    email:    str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int
    user_id:      str
    role:         str


# ── Vitals ────────────────────────────────────────────────
class VitalsInput(BaseModel):
    heart_rate:    int   = Field(..., ge=30,   le=250)
    systolic_bp:   int   = Field(..., ge=60,   le=250)
    diastolic_bp:  int   = Field(..., ge=40,   le=150)
    spo2:          float = Field(..., ge=60.0, le=100.0)
    temperature:   float = Field(..., ge=95.0, le=110.0)
    glucose:       float = Field(..., ge=50.0, le=600.0)
    weight:        float = Field(..., ge=20.0, le=300.0)
    height:        float = Field(..., ge=100.0,le=250.0)


# ── Lifestyle ─────────────────────────────────────────────
class LifestyleInput(BaseModel):
    sleep_hours:              float = Field(..., ge=0.0, le=24.0)
    exercise_days_per_week:   int   = Field(..., ge=0,   le=7)
    diet_quality:             int   = Field(..., ge=1,   le=10)
    hydration_liters:         float = Field(..., ge=0.0, le=10.0)
    stress_level:             int   = Field(..., ge=1,   le=10)
    smoking:                  bool  = False
    alcohol_units_per_week:   int   = Field(default=0, ge=0, le=100)


# ── Patient ───────────────────────────────────────────────
class PatientProfile(BaseModel):
    name:                str
    age:                 int   = Field(..., ge=0, le=150)
    gender:              str   = "unknown"
    blood_group:         str   = ""
    location:            str   = ""
    vitals:              VitalsInput
    lifestyle:           LifestyleInput
    family_history:      list[str] = []
    medical_history:     list[str] = []
    current_medications: list[str] = []
    allergies:           list[str] = []


# ── Risk Prediction ───────────────────────────────────────
class DiseaseRiskScore(BaseModel):
    disease:              str
    probability:          float
    confidence:           float
    risk_level:           RiskLevel
    contributing_factors: list[dict[str, Any]] = []
    risk_explanation:     str | None = None

class RiskPredictionResponse(BaseModel):
    patient_id:      str
    health_score:    int
    overall_risk:    RiskLevel
    disease_risks:   list[DiseaseRiskScore]
    ai_summary:      str
    recommendations: list[str]
    timestamp:       datetime = Field(default_factory=datetime.utcnow)


# ── Chat ──────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role:    str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    messages:        list[ChatMessage]
    patient_context: dict[str, Any] | None = None
    language:        str = "en"

class ChatResponse(BaseModel):
    reply:           str
    tokens_used:     int
    model:           str
    response_time_ms:int
    sources:         list[dict] = []      # RAG: retrieved guideline cards used
    rag_enabled:     bool       = False   # whether RAG retrieval was active


# ── Report ────────────────────────────────────────────────
class AbnormalMetric(BaseModel):
    parameter:      str
    value:          str
    normal_range:   str
    severity:       str
    interpretation: str

class ReportAnalysisResponse(BaseModel):
    raw_text:          str
    abnormal_metrics:  list[AbnormalMetric]
    ai_interpretation: str
    risk_assessment:   str
    recommendations:   list[str]
    confidence_score:  float
    processing_time_ms:int


# ── What-If ───────────────────────────────────────────────
class WhatIfRequest(BaseModel):
    current_profile:  PatientProfile
    proposed_changes: LifestyleInput
    simulation_years: int = Field(default=1, ge=1, le=10)

class WhatIfResponse(BaseModel):
    current_health_score:        int
    projected_health_score:      int
    score_delta:                 int
    risk_changes:                dict[str, float]
    life_expectancy_impact_years:float
    ai_explanation:              str
    milestones:                  list[dict[str, str]]
    effect_confidence:           str = "moderate"   # low/moderate/high — based on profile completeness
    causal_assumptions:          list[str] = []      # what's held constant in this estimate


# ── Multi-Agent Specialist Consensus ────────────────────────
class AgentOpinion(BaseModel):
    role:           str
    recommendation: str
    confidence:     float          # 0-1
    focus_risks:    list[str] = []

class ConsensusResponse(BaseModel):
    patient_name:          str
    agents:                list[AgentOpinion]
    consensus_summary:     str
    points_of_agreement:   list[str]
    points_of_divergence:  list[str]


# ── Triage ────────────────────────────────────────────────
class TriagePatient(BaseModel):
    patient_id:   str
    name:         str
    age:          int
    condition:    str
    vitals:       VitalsInput
    arrival_time: datetime = Field(default_factory=datetime.utcnow)
    notes:        str = ""

class TriageScore(BaseModel):
    patient_id:        str
    name:              str
    triage_score:      int
    triage_level:      TriageLevel
    priority_rank:     int
    alert_message:     str
    recommended_action:str


# ── Recommendations ───────────────────────────────────────
class RecommendationRequest(BaseModel):
    patient_profile: PatientProfile
    category:        str = Field(..., pattern="^(diet|exercise|sleep|stress|preventive)$")

class RecommendationResponse(BaseModel):
    category:             str
    plan:                 list[str]
    rationale:            str
    duration_weeks:       int
    expected_improvement: str
    ai_confidence:        float


# ═══════════════════════════════════════════════════════════
#  MODULE: Real ML Validation Engine (trained models + SHAP)
# ═══════════════════════════════════════════════════════════
class MLFeatureContribution(BaseModel):
    feature:      str
    value:        float
    contribution: float
    direction:    str   # "increases_risk" | "decreases_risk"

class MLPredictionResponse(BaseModel):
    disease:              str
    probability_pct:      float
    model_used:           str
    dataset_name:         str
    data_source:          str   # "local_file" | "downloaded" | "offline_fallback"
    model_accuracy:       float
    model_roc_auc:        float
    explanation_method:   str
    interpretation_note:  str
    top_factors:          list[MLFeatureContribution]

class CrossValidationResponse(BaseModel):
    ml_probability_pct:        float
    clinical_probability_pct:  float | None
    clinical_tool:              str | None
    agreement_delta_points:     float | None
    agreement_label:            str
    ml_details:                  MLPredictionResponse

class ConfusionMatrixData(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int

class ROCPoint(BaseModel):
    fpr: float
    tpr: float

class ModelComparisonEntry(BaseModel):
    accuracy: float
    f1:       float
    roc_auc:  float

class MLModelMetrics(BaseModel):
    disease: str
    disease_key: str
    dataset_name: str
    data_source: str
    n_samples: int
    n_features: int
    positive_rate: float
    feature_names: list[str]
    best_model: str
    model_kind: str
    explainability_method: str
    all_models_compared: dict[str, ModelComparisonEntry]
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: ConfusionMatrixData
    roc_curve: list[ROCPoint]
    global_feature_importance: list[dict[str, Any]]
    trained_at: str
    training_time_ms: int

class MLPredictRequest(BaseModel):
    patient_profile: PatientProfile


# ── Health Twin ───────────────────────────────────────────
class HealthTwinResponse(BaseModel):
    patient_id:        str
    health_score:      int
    risk_level:        RiskLevel
    disease_risks:     dict[str, float]
    ai_clinical_summary: str
    preventive_actions:  list[dict[str, Any]]


# ═══════════════════════════════════════════════════════════
#  MODULE 1 — Generational Health Twin (Family Intelligence)
# ═══════════════════════════════════════════════════════════
class FamilyMember(BaseModel):
    id:               str               # e.g. "father", "paternal_grandfather", "sibling_1"
    relation:         str               # human-readable: "Father", "Paternal Grandfather"
    generation:       int               # -2 grandparent, -1 parent, 0 self/sibling, +1 child
    name:             str = ""
    age:              int | None = None
    alive:            bool = True
    age_at_death:     int | None = None
    cause_of_death:   str = ""
    conditions:       list[str] = []          # e.g. ["Type 2 Diabetes", "Hypertension"]
    age_at_diagnosis: dict[str, int] = {}      # {"Type 2 Diabetes": 52}

class FamilyHealthGraphRequest(BaseModel):
    patient:        PatientProfile
    family_members: list[FamilyMember]

class ContributingRelative(BaseModel):
    relation:   str
    condition:  str
    age_at_diagnosis: int | None = None
    weight:     float

class HereditaryRiskItem(BaseModel):
    disease:                str
    base_risk:              float   # patient's own clinical risk %, from clinical_risk_service
    hereditary_multiplier:  float
    adjusted_risk:          float
    contributing_relatives: list[ContributingRelative] = []

class FamilyTreeNode(BaseModel):
    id:          str
    relation:    str
    generation:  int
    name:        str
    age:         int | None = None
    alive:       bool = True
    conditions:  list[str] = []
    risk_score:  float = 0.0   # 0-100, for heatmap coloring
    risk_band:   str = "low"   # low / moderate / high / critical

class InheritancePath(BaseModel):
    disease:    str
    from_member:str           # relation of the relative
    to_member:  str = "Self"
    strength:   float          # 0-1, visual line thickness

class HereditaryRiskResponse(BaseModel):
    patient_id:              str
    hereditary_risks:        list[HereditaryRiskItem]
    family_tree:             list[FamilyTreeNode]
    inheritance_paths:       list[InheritancePath]
    family_preventive_actions: list[dict[str, Any]]
    next_generation_risk:    dict[str, float]
    ai_summary:              str


# ═══════════════════════════════════════════════════════════
#  MODULE 2 — Health Time Machine (Future Self Engine)
# ═══════════════════════════════════════════════════════════
class TimeMachineRequest(BaseModel):
    current_profile:    PatientProfile
    years:              int = Field(..., description="1, 5, or 10")
    apply_prevention:   list[str] = []   # action ids from Module 3, optional "Future B"

class OrganHealth(BaseModel):
    organ:          str
    current_pct:    int
    future_pct:     int
    delta:          int

class DiseaseProgression(BaseModel):
    disease:        str
    current_risk:   float
    future_risk:    float
    delta:          float
    tool_used:      str

class TimeMachineResponse(BaseModel):
    patient_id:           str
    current_age:          int
    future_age:           int
    years_projected:      int
    current_health_score: int
    future_health_score:  int
    current_biological_age: int
    future_biological_age:  int
    organ_health:         list[OrganHealth]
    disease_progression:  list[DiseaseProgression]
    ai_narrative:         str
    scenario:             str   # "status_quo" or "with_prevention"


# ═══════════════════════════════════════════════════════════
#  MODULE 3 — AI Preventive Impact Engine (ROI Calculator)
# ═══════════════════════════════════════════════════════════
class PreventiveActionInput(BaseModel):
    current_profile: PatientProfile
    action_ids:      list[str]   # e.g. ["sleep_8h", "walk_10k", "reduce_sugar"]

class ActionDefinition(BaseModel):
    id:          str
    label:       str
    description: str
    icon:        str

class RiskReductionItem(BaseModel):
    disease:        str
    before_pct:     float
    after_pct:      float
    reduction_pct:  float          # absolute percentage-point reduction
    relative_reduction_pct: float  # RRR %

class CostSavingItem(BaseModel):
    disease:            str
    avoided_risk_points:float
    avg_treatment_cost_inr: float
    estimated_savings_inr: float
    basis:              str

class PreventiveImpactResponse(BaseModel):
    patient_id:                 str
    selected_actions:           list[str]
    health_score_before:        int
    health_score_after:         int
    health_score_increase:      int
    risk_reductions:            list[RiskReductionItem]
    life_expectancy_gain_years: float
    cost_savings_breakdown:     list[CostSavingItem]
    total_cost_savings_inr:     float
    ai_narrative:               str
    assumptions:                list[str]

# ── Parallel Universe Simulator ────────────────────────────
class TimelineConfig(BaseModel):
    label:       str
    description: str
    color:       str = "#00e5ff"
    lifestyle_overrides: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"smoking": false, "sleep_hours": 8, "exercise_days_per_week": 5}

class YearDataPoint(BaseModel):
    year:           int
    age:            int
    health_score:   int
    risks:          dict[str, float]
    biological_age: int

class TimelineResult(BaseModel):
    timeline_id:  int
    label:        str
    description:  str
    color:        str
    trajectory:   list[YearDataPoint]
    endpoint_summary: dict[str, Any]   # 10-year snapshot

class ParallelSimRequest(BaseModel):
    base_profile: PatientProfile
    timelines:    list[TimelineConfig] = Field(default_factory=list)
    years:        int = 10

class ParallelSimResponse(BaseModel):
    patient_name: str
    patient_age:  int
    timelines:    list[TimelineResult]
    ai_narrative: str

# ── Wearable Digital Twin ──────────────────────────────────
class WearableReading(BaseModel):
    timestamp:       str
    heart_rate:      int
    spo2:            float
    steps_today:     int
    stress_score:    int        # 0-100
    sleep_last_night:float
    hrv_ms:          int        # heart rate variability
    skin_temp_c:     float
    anomaly:         str | None = None

class WearableStreamRequest(BaseModel):
    patient_name:   str
    base_profile:   PatientProfile
    duration_seconds: int = 30   # how many readings to generate

# ── Population Health Intelligence ────────────────────────
class DistrictHealthData(BaseModel):
    district:        str
    state:           str
    lat:             float
    lng:             float
    diabetes_prev:   float    # prevalence %
    hypertension_prev: float
    heart_prev:      float
    risk_index:      float    # composite 0-100
    population:      int
    alert:           str | None = None

class FedLearningResponse(BaseModel):
    rounds:          list[FedRoundResult]
    final_accuracy:  float
    total_patients:  int
    privacy_guarantee: str
    ai_narrative:    str
    simulation_note: str = (
        "Architecture Simulator: training rounds are narrative demonstrations of "
        "federated gradient aggregation. No real distributed ML occurs in this build. "
        "Production deployment would use PySyft or Flower."
    )


class PopHealthResponse(BaseModel):
    districts:       list[DistrictHealthData]
    national_avg:    dict[str, float]
    top_alerts:      list[str]
    resource_gaps:   list[str]
    data_note: str = (
        "District data is synthetic/illustrative, derived from ICMR-INDIAB 2023 "
        "and NFHS-5 patterns. Production version accepts real hospital CSV uploads."
    )

# ── Federated Learning Narrative ──────────────────────────
class FedHospital(BaseModel):
    id:            str
    name:          str
    city:          str
    patients:      int
    rounds_trained: int
    local_accuracy: float
    privacy_score:  float    # 0-100 (100 = perfectly private)

class FedRoundResult(BaseModel):
    round_num:       int
    global_accuracy: float
    accuracy_delta:  float
    hospitals:       list[FedHospital]
    privacy_budget_used: float   # epsilon (DP budget)

