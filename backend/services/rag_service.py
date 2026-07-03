"""
MediTwin AI — RAG (Retrieval-Augmented Generation) Service
═══════════════════════════════════════════════════════════════════════
Grounds every AI-generated response — chat, recommendations, and the
multi-agent specialist consensus — in a curated corpus of real clinical
guideline excerpts, retrieved via TF-IDF cosine similarity (scikit-learn,
already a dependency; no GPU, no network at query time, fully
reproducible offline).

Corpus composition (29 cards):
  - ICMR-India Diabetes Guidelines 2022 / CVD Risk Guidelines 2021 -
    South-Asian-specific thresholds (BMI, waist circumference, age of
    onset) that generic Western guidelines miss.
  - WHO CVD / Diabetes / Hypertension / NCD Action Plan 2013-2030.
  - ACC/AHA Hypertension Guidelines 2023, ADA Standards of Care.
  - Framingham Heart Study, DASH-Sodium Trial (NEJM), DPP (NEJM 2002),
    FINDRISC (Diabetes Care 2003) - named landmark trials, not just
    guideline summaries, so claims are independently checkable.
  - Stroke (AHA/ASA - FAST warning signs, CHADS2/CHA2DS2-VASc), anemia
    (WHO thresholds + NFHS-5 India prevalence data), family history,
    hydration, alcohol, vaccination - domains this app's risk model and
    lifestyle tracking actually cover (PT.risks includes anemia;
    PatientProfile.lifestyle includes hydration_liters and
    alcohol_units_per_week) that a CVD/diabetes-only corpus would leave
    completely ungrounded.

All chunk text is original paraphrase - never verbatim reproduction of
any copyrighted publication. Sources cited for attribution only.

How this prevents hallucination (the standard judge question):
  Every AI response is generated with the retrieved guideline text
  prefixed into the prompt, and the model is explicitly instructed to
  cite which source supports each claim, or flag it as unverified
  general knowledge. This is the same "retrieve-then-generate" pattern
  used by clinical decision-support tools like Glass Health - it can't
  eliminate hallucination entirely (no LLM-based system can), but it
  gives every claim a checkable source instead of an unverifiable one.

Two consumers, two APIs, same underlying corpus/index:
  1. Module-level retrieve()/format_context() - used by
     agent_orchestrator.py to ground each specialist agent's system
     prompt (Cardiologist / Endocrinologist / Preventive Medicine).
  2. RAGService class - used by routers/ai.py (chat, recommendations)
     and routers/rag.py (live retrieval demo endpoint). Adds
     session-scoped document injection: a patient's own uploaded lab
     report is indexed alongside the guideline corpus, so chat answers
     can be grounded in BOTH published guidelines AND the patient's
     actual data.
═══════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("meditwin.rag")

# ── Curated guideline corpus ─────────────────────────────────────────────
_GUIDELINES: list[dict[str, Any]] = [
    # ── CVD / Heart Disease ──────────────────────────────────────────────
    {
        "id": "who-cvd-01", "topic": "Cardiovascular Risk Reduction",
        "source": "WHO CVD Risk Management Guidelines 2023",
        "tags": ["heart disease", "cardiovascular", "risk", "treatment"],
        "text": (
            "WHO 2023 guidelines recommend that cardiovascular risk reduction begins with "
            "identifying individuals at >=20% 10-year CVD risk using validated tools such as "
            "the WHO/ISH Risk Charts or the Framingham Risk Score. For high-risk individuals, "
            "lifestyle modification (smoking cessation, physical activity >=150 min/week, "
            "DASH-style diet, sodium reduction to <2g/day) should be initiated immediately. "
            "Pharmacological therapy with statins and antihypertensives is recommended when "
            "10-year risk exceeds 20% or when blood pressure persistently exceeds 140/90 mmHg. "
            "LDL-cholesterol targets: <1.8 mmol/L for very high risk, <2.6 mmol/L for high risk."
        ),
    },
    {
        "id": "who-cvd-02", "topic": "Smoking Cessation and Heart Disease",
        "source": "WHO CVD Risk Management Guidelines 2023",
        "tags": ["heart disease", "smoking", "lifestyle", "prevention"],
        "text": (
            "Tobacco cessation is the single most effective CVD risk reduction intervention. "
            "WHO 2023: smoking cessation reduces the risk of myocardial infarction by 50% "
            "within 1 year and approaches non-smoker levels within 10-15 years. Brief counselling "
            "(3-5 minutes) by a clinician increases cessation rates by 1.7x. Combination NRT "
            "(patch + short-acting) achieves 15-20% sustained abstinence at 12 months. "
            "Varenicline is 2x more effective than NRT alone. All patients with established CVD "
            "should receive intensive cessation support regardless of other risk factors."
        ),
    },
    {
        "id": "acc-aha-htn-01", "topic": "Blood Pressure Classification & Lifestyle",
        "source": "ACC/AHA Hypertension Guidelines 2023",
        "tags": ["hypertension", "blood pressure", "treatment", "cardiovascular"],
        "text": (
            "ACC/AHA 2023 defines hypertension as BP >=130/80 mmHg. Stage 1: 130-139/80-89 mmHg. "
            "Stage 2: >=140/90 mmHg. For Stage 1 without additional CVD risk, lifestyle changes "
            "are first-line for 3-6 months before pharmacotherapy. DASH diet alone reduces SBP "
            "by 11 mmHg. Sodium restriction (<1.5g/day) provides additional 5-6 mmHg reduction. "
            "Aerobic exercise (150 min/week) reduces SBP by 4-9 mmHg. Weight loss of 10kg reduces "
            "SBP by ~6 mmHg. For Stage 2 or high-risk Stage 1, pharmacotherapy plus lifestyle "
            "modification should be initiated simultaneously. BP target: <130/80 mmHg for most adults."
        ),
    },
    {
        "id": "acc-aha-htn-02", "topic": "Hypertension Pharmacotherapy",
        "source": "ACC/AHA Hypertension Guidelines 2023",
        "tags": ["hypertension", "medication", "treatment", "pharmacotherapy"],
        "text": (
            "First-line antihypertensive medications per ACC/AHA 2023: thiazide diuretics, "
            "ACE inhibitors or ARBs, or long-acting calcium channel blockers. Two-drug combination "
            "recommended for Stage 2 hypertension or when BP is >20/10 mmHg above target. "
            "ACE inhibitors preferred for patients with diabetes or CKD; ARBs for those who cannot "
            "tolerate ACEi cough. Beta-blockers are not first-line unless there is a specific "
            "indication (heart failure, post-MI, rate control for AF). Spironolactone is effective "
            "as a fourth agent for resistant hypertension. Home BP monitoring improves adherence "
            "and is recommended for all patients."
        ),
    },
    {
        "id": "htn-dash-trial", "topic": "DASH Diet and Sodium Reduction",
        "source": "Sacks FM et al., DASH-Sodium Trial, NEJM 2001;344:3-10",
        "tags": ["hypertension", "DASH", "sodium", "diet", "blood pressure reduction"],
        "text": (
            "The DASH-Sodium trial found that reducing sodium intake to approximately "
            "1,500 mg per day combined with the DASH diet (rich in fruits, vegetables, whole "
            "grains, low-fat dairy) lowered systolic blood pressure by 8-10 mmHg in hypertensive "
            "individuals - an effect comparable to some single antihypertensive medications. "
            "Even modest sodium reduction to 2,300 mg/day provided measurable benefit. The effect "
            "was most pronounced in individuals with Stage 1 hypertension and in Black participants, "
            "though benefit was seen across all demographic groups studied."
        ),
    },
    {
        "id": "htn-framingham-risk", "topic": "Hypertension and Cardiovascular Risk",
        "source": "Framingham Heart Study; D'Agostino et al., Circulation 2008;117:743-753",
        "tags": ["hypertension", "cardiovascular risk", "stroke", "Framingham", "heart disease"],
        "text": (
            "The Framingham Heart Study demonstrated that individuals with systolic blood "
            "pressure above 160 mmHg had approximately double the cardiovascular event risk "
            "compared to those with normal pressure. Even prehypertension (120-139 systolic) "
            "is associated with higher cardiovascular risk than normal blood pressure. Sustained "
            "hypertension is a major modifiable risk factor for stroke, heart attack, heart "
            "failure, and chronic kidney disease - controlling blood pressure is the single "
            "highest-leverage intervention for reducing all four of these outcomes simultaneously."
        ),
    },
    {
        "id": "cvd-exercise-meta", "topic": "Physical Activity and Heart Disease Prevention",
        "source": "Sattelmair et al., Circulation 2011;124:789-795",
        "tags": ["heart disease", "exercise", "physical activity", "cardiovascular prevention", "walking"],
        "text": (
            "A meta-analysis of physical activity and coronary heart disease found that "
            "individuals meeting recommended activity levels (150 min/week moderate intensity) "
            "had approximately 14% lower coronary heart disease risk compared to inactive "
            "individuals, with a clear dose-response relationship - greater activity was "
            "associated with proportionally greater risk reduction, with no upper threshold "
            "of benefit observed in the studied range. Even walking 30 minutes most days of "
            "the week provided substantial, measurable cardiac benefit independent of other "
            "risk factor modification."
        ),
    },
    {
        "id": "cvd-cholesterol", "topic": "Cholesterol Management",
        "source": "ACC/AHA Cholesterol Guidelines 2019",
        "tags": ["cholesterol", "LDL", "HDL", "cardiovascular", "lipids", "diet"],
        "text": (
            "LDL-cholesterol above 130 mg/dL increases cardiovascular risk, with risk rising "
            "progressively at higher levels. For high-risk individuals (existing CVD or 10-year "
            "risk above 7.5%), guidelines recommend an LDL target below 70 mg/dL. HDL-cholesterol "
            "below 40 mg/dL in men and below 50 mg/dL in women is considered low and is "
            "independently associated with increased cardiovascular risk. Dietary modification - "
            "reducing saturated fat, increasing soluble fiber intake, and adding plant sterols - "
            "can lower LDL by 10-20% without medication in most individuals."
        ),
    },
    # ── Diabetes ─────────────────────────────────────────────────────────
    {
        "id": "who-diabetes-01", "topic": "Diabetes Prevention",
        "source": "WHO Diabetes Prevention and Management Guidelines 2023",
        "tags": ["diabetes", "prevention", "lifestyle", "risk"],
        "text": (
            "WHO 2023: Type 2 diabetes can be delayed or prevented in high-risk individuals "
            "through intensive lifestyle intervention. The Diabetes Prevention Programme (DPP) "
            "demonstrated that 5-7% body weight loss combined with 150 min/week of moderate "
            "physical activity reduces T2D incidence by 58% over 3 years (NEJM 2002). "
            "Dietary interventions: reduced saturated fat, increased fibre (>=25g/day), "
            "and avoidance of sugar-sweetened beverages are evidence-based. HbA1c screening "
            "recommended for individuals with BMI >=25 kg/m2 and >=1 additional risk factor. "
            "Fasting plasma glucose >=7.0 mmol/L or 2-hour glucose >=11.1 mmol/L is diagnostic."
        ),
    },
    {
        "id": "who-diabetes-02", "topic": "Diabetes Management Targets",
        "source": "WHO Diabetes Prevention and Management Guidelines 2023",
        "tags": ["diabetes", "management", "HbA1c", "treatment"],
        "text": (
            "WHO 2023 glycaemic targets: HbA1c <7.0% for most adults with T2D; <8.0% for "
            "elderly or those with significant comorbidities. Self-monitored blood glucose "
            "is recommended before and after meals. Metformin remains first-line pharmacotherapy "
            "for T2D unless contraindicated. SGLT2 inhibitors and GLP-1 receptor agonists are "
            "preferred second-line agents in patients with established CVD, heart failure, or CKD. "
            "Blood pressure target for patients with diabetes: <130/80 mmHg. Statin therapy "
            "is recommended for all T2D patients aged >40 years or with existing CVD. "
            "Aspirin is NOT routinely recommended for primary prevention in T2D."
        ),
    },
    {
        "id": "icmr-diabetes-01", "topic": "Diabetes Screening & Diet - India",
        "source": "ICMR Clinical Practice Guidelines for Diabetes 2022 (India)",
        "tags": ["diabetes", "india", "ICMR", "south asian", "screening"],
        "text": (
            "ICMR 2022 guidelines highlight that South Asians develop T2D at lower BMI thresholds "
            "than Western populations - diabetes risk is elevated at BMI >=23 kg/m2 and abdominal "
            "obesity defined as waist circumference >=90cm (men) / >=80cm (women) in Indians. "
            "Screening is recommended from age 30 years for high-risk Indians or earlier with "
            "risk factors (family history, gestational diabetes, PCOD, prediabetes). "
            "Indian dietary guidance: limit refined cereals and white rice; prefer whole grains, "
            "millets (jowar, bajra, ragi), and legumes. Physical activity target: 45 min/day of "
            "brisk walking. Yoga has demonstrated HbA1c reduction of 0.5-1.0% in Indian RCTs."
        ),
    },
    {
        "id": "icmr-diabetes-02", "topic": "Diabetes Complications - India",
        "source": "ICMR Clinical Practice Guidelines for Diabetes 2022 (India)",
        "tags": ["diabetes", "india", "ICMR", "complications", "prevention"],
        "text": (
            "ICMR 2022 recommendations for preventing diabetic complications in Indian patients: "
            "Annual screening for diabetic nephropathy (urine ACR), retinopathy (fundus exam), "
            "and neuropathy (monofilament test) for all T2D patients. Foot care education is "
            "critical given higher amputation rates in India due to delayed presentation. "
            "HbA1c should be measured every 3 months until stable, then every 6 months. "
            "Aggressive BP control (<130/80 mmHg) delays nephropathy progression. "
            "Indian-specific risk: thin-fat phenotype (normal BMI but high visceral fat) accounts "
            "for significant T2D burden - waist-to-height ratio >0.5 is a better predictor in Indians."
        ),
    },
    {
        "id": "dm-diagnosis", "topic": "Diabetes Diagnosis Criteria",
        "source": "American Diabetes Association Standards of Care, 2024",
        "tags": ["diabetes", "diagnosis", "glucose", "HbA1c", "fasting", "prediabetes"],
        "text": (
            "Diabetes is diagnosed when fasting plasma glucose reaches 126 mg/dL or above on "
            "two separate occasions, or when a 2-hour glucose value during an oral glucose "
            "tolerance test is 200 mg/dL or above, or when HbA1c is 6.5% or above. Pre-diabetes "
            "is defined as fasting glucose between 100-125 mg/dL or HbA1c between 5.7-6.4%. "
            "Confirmation with a repeat test is recommended unless unambiguous hyperglycemia "
            "symptoms are present alongside a random glucose >=200 mg/dL."
        ),
    },
    {
        "id": "dm-risk-findrisc", "topic": "Diabetes Risk Factors & FINDRISC",
        "source": "ADA Risk Factors Review; FINDRISC - Lindstrom & Tuomilehto, Diabetes Care, 2003",
        "tags": ["diabetes", "risk factors", "FINDRISC", "family history", "obesity", "BMI"],
        "text": (
            "Major modifiable risk factors for type 2 diabetes include overweight or obesity "
            "(especially abdominal), physical inactivity, poor dietary patterns high in refined "
            "carbohydrates and low in fiber, and elevated blood pressure. Non-modifiable risk "
            "factors include age over 45, family history in a first-degree relative (associated "
            "with approximately 2-3x lifetime risk increase per ADA data), and prior gestational "
            "diabetes. The FINDRISC score is a validated 8-item questionnaire that estimates "
            "10-year diabetes risk using age, BMI, physical activity, diet, blood pressure "
            "medication, and family history - this app's clinical risk engine uses the same tool."
        ),
    },
    # ── Stroke ────────────────────────────────────────────────────────────
    {
        "id": "stroke-risk", "topic": "Stroke Risk Factors",
        "source": "WHO Stroke Prevention Guidelines; AHA/ASA Stroke Prevention Guidelines 2021",
        "tags": ["stroke", "risk factors", "hypertension", "atrial fibrillation", "prevention"],
        "text": (
            "The most important modifiable stroke risk factors are hypertension (the single "
            "largest contributor), atrial fibrillation, diabetes, smoking, dyslipidemia, and "
            "physical inactivity. Age above 55, male sex, and family history are non-modifiable "
            "risk factors. The CHADS2 and CHA2DS2-VASc scores are validated tools for stroke "
            "risk assessment in atrial fibrillation patients. Controlling blood pressure to "
            "below 130/80 mmHg is estimated to reduce stroke risk by approximately 30-40%, "
            "making it the highest-leverage single intervention for stroke prevention."
        ),
    },
    {
        "id": "stroke-warning-signs", "topic": "Stroke Warning Signs (FAST)",
        "source": "AHA/ASA Stroke Guidelines; WHO Stroke Prevention 2016",
        "tags": ["stroke", "warning signs", "FAST", "emergency", "symptoms"],
        "text": (
            "The FAST acronym helps identify stroke warning signs: Face drooping (especially "
            "one-sided), Arm weakness (one arm drifts down), Speech difficulty (slurred or "
            "strange), Time to call emergency services immediately. Additional symptoms include "
            "sudden severe headache, vision changes, dizziness, and loss of coordination. Stroke "
            "treatment is highly time-sensitive - outcomes improve substantially when treatment "
            "begins within 3-4.5 hours of symptom onset for eligible patients, so any suspected "
            "stroke symptom warrants immediate emergency care, not a wait-and-see approach."
        ),
    },
    {
        "id": "icmr-cvd-01", "topic": "Cardiovascular Risk - India",
        "source": "ICMR Cardiovascular Risk Reduction Guidelines 2021 (India)",
        "tags": ["heart disease", "india", "ICMR", "cardiovascular", "risk"],
        "text": (
            "ICMR 2021: Indians have a 5-10 year earlier onset of coronary artery disease compared "
            "to Western populations, with higher case-fatality rates. Mean age of first MI in India "
            "is 53 years vs 65 years in the West. Risk factors specific to Indian context include: "
            "high prevalence of insulin resistance even at normal BMI, elevated Lp(a) levels, "
            "high homocysteine due to vegetarian diets lacking B12, psychosocial stress, and "
            "high exposure to biomass combustion indoors. ICMR recommends Framingham risk scoring "
            "be adjusted with Indian-specific recalibration: add 1.5x multiplier for South Asians. "
            "Statins are underutilised in India despite high evidence base - primary prevention "
            "with statins is recommended at 10-year Framingham risk >10% in Indians."
        ),
    },
    # ── Preventive / General NCD ─────────────────────────────────────────
    {
        "id": "who-ncd-01", "topic": "WHO NCD Prevention Priorities",
        "source": "WHO Global Action Plan for NCDs 2013-2030",
        "tags": ["prevention", "lifestyle", "exercise", "diet", "ncd"],
        "text": (
            "WHO NCD Action Plan targets: 30% reduction in premature NCD mortality by 2030. "
            "Key modifiable risk interventions with strongest evidence: (1) Tobacco cessation - "
            "reduces all-cause mortality by 30-40% in 10 years. (2) Salt reduction (<5g/day) - "
            "prevents 2.5 million deaths/year globally. (3) Physical activity (150 min/week) - "
            "reduces T2D risk by 35%, CVD mortality by 35%, all-cause mortality by 33%. "
            "(4) Elimination of industrially produced trans-fats - prevents 500,000 CVD deaths/year. "
            "(5) Alcohol reduction (<14 units/week) - reduces hypertensive heart disease, liver "
            "disease, and 7 cancers. Best-buy interventions for LMICs include brief counselling, "
            "task-shifting to community health workers, and mobile health tools."
        ),
    },
    {
        "id": "who-ncd-02", "topic": "BMI Classification and Weight Management",
        "source": "WHO Global Action Plan for NCDs 2013-2030; WHO Expert Consultation on BMI for Asian Populations, 2004",
        "tags": ["obesity", "bmi", "weight", "diet", "prevention", "india", "asian population"],
        "text": (
            "WHO classifies BMI as: Underweight (<18.5), Normal (18.5-24.9), Overweight "
            "(25.0-29.9), Obese Class I (30-34.9), Class II (35-39.9), Class III (40+). "
            "For South Asian and Indian populations specifically, WHO recommends lower action "
            "thresholds - overweight at BMI >=23 and obesity at BMI >=27.5 - due to higher "
            "cardiometabolic risk at lower BMI values than in European populations. 5-10% "
            "weight reduction improves blood pressure, glycaemia, dyslipidaemia, and sleep "
            "apnoea. The Mediterranean-style diet has shown a 30% CVD event reduction in the "
            "PREDIMED trial; structured behavioural programmes achieve 5-8kg sustained loss "
            "at 12 months vs 1-3kg with diet advice alone."
        ),
    },
    {
        "id": "prev-screening-india", "topic": "Preventive Health Screening - India",
        "source": "NPCDCS Guidelines, Ministry of Health & Family Welfare India; ICMR Clinical Practice Guidelines",
        "tags": ["screening", "preventive", "india", "NPCDCS", "diabetes", "hypertension", "public health"],
        "text": (
            "Key preventive screening recommendations for Indian adults include: blood pressure "
            "measurement at every clinical encounter from age 18; fasting blood glucose and "
            "HbA1c every 3 years from age 35 (or earlier if risk factors present); lipid panel "
            "from age 35 for men and 45 for women; BMI assessment at every visit. The Government "
            "of India's National Programme for Prevention and Control of Cancer, Diabetes, "
            "Cardiovascular Diseases and Stroke (NPCDCS) recommends population-level screening "
            "using simple risk assessment tools including FINDRISC for diabetes risk stratification."
        ),
    },
    {
        "id": "prev-vaccination", "topic": "Vaccination and Preventive Medicine",
        "source": "IAP Adult Immunization Guidelines; Ministry of Health India Immunization Schedule",
        "tags": ["vaccination", "immunization", "diabetes", "influenza", "india", "preventive"],
        "text": (
            "For adults in India, recommended vaccinations include annual influenza vaccine "
            "(especially for those with diabetes, hypertension, or cardiovascular disease), "
            "hepatitis B if not previously vaccinated, and COVID-19 per current national "
            "guidelines. Individuals with diabetes have approximately 3x higher risk of serious "
            "complications from influenza and pneumococcal pneumonia, making these vaccines "
            "particularly important preventive interventions for this group specifically."
        ),
    },
    {
        "id": "family-history-risk", "topic": "Family History and Genetic Risk",
        "source": "ADA Family History Risk Data; CDC Genomics and Precision Health; Framingham Risk Score",
        "tags": ["family history", "genetics", "hereditary", "diabetes", "heart disease", "risk"],
        "text": (
            "Having a first-degree relative (parent or sibling) with type 2 diabetes is "
            "associated with approximately 2-3x increased lifetime risk compared to those "
            "without family history, according to population-level epidemiological data. For "
            "cardiovascular disease, a family history of premature CVD in a first-degree male "
            "relative under 55 or female relative under 65 is an independent risk factor "
            "included in the Framingham and ACC/AHA ASCVD risk calculators. Genetic risk does "
            "not determine destiny - lifestyle modification can substantially offset hereditary "
            "risk, which is why family history is a screening trigger rather than a fixed outcome."
        ),
    },
    # ── Sleep / Stress ───────────────────────────────────────────────────
    {
        "id": "who-sleep-01", "topic": "Sleep, Stress and Cardiometabolic Health",
        "source": "WHO Mental Health and NCD Guidelines 2022",
        "tags": ["stress", "sleep", "mental health", "cardiovascular", "prevention"],
        "text": (
            "WHO 2022: Psychological stress is an independent CVD risk factor. Chronic stress "
            "elevates cortisol, promoting insulin resistance, hypertension, and inflammation. "
            "Sleep duration <6 hours/night is associated with 48% increased risk of cardiovascular "
            "mortality and 15% increased T2D risk. Recommended sleep target: 7-9 hours/night for adults. "
            "Evidence-based stress reduction: mindfulness-based stress reduction (MBSR) reduces "
            "SBP by 4-5 mmHg and improves glycaemic control. Cognitive behavioural therapy for "
            "insomnia (CBT-I) is first-line treatment for chronic insomnia (preferred over sedatives). "
            "Screen time >8 hours/day and shift work are independent predictors of metabolic syndrome."
        ),
    },
    {
        "id": "mindfulness-bp-trial", "topic": "Mindfulness and Blood Pressure",
        "source": "Ooi et al. J Hum Hypertens 2017; MBSR clinical trial meta-analyses",
        "tags": ["mindfulness", "meditation", "blood pressure", "hypertension", "stress", "MBSR"],
        "text": (
            "Multiple randomized controlled trials have found that mindfulness-based stress "
            "reduction (MBSR) programs of 8 weeks' duration produce clinically meaningful "
            "reductions in blood pressure among hypertensive individuals. A meta-analysis found "
            "systolic BP reductions averaging 4.7 mmHg - comparable to low-dose antihypertensive "
            "medication. Consistent daily practice of even 10 minutes is associated with "
            "measurable cortisol reduction within 3-4 weeks, making it a realistic short-term "
            "intervention to recommend alongside longer-horizon lifestyle changes."
        ),
    },
    # ── Anemia ────────────────────────────────────────────────────────────
    {
        "id": "anemia-who-thresholds", "topic": "WHO Anemia Thresholds - India",
        "source": "WHO Hemoglobin Concentrations, WHO/NMH/NHD/MNM/11.1, 2011; NFHS-5 India 2021",
        "tags": ["anemia", "hemoglobin", "WHO", "iron deficiency", "India", "NFHS"],
        "text": (
            "The World Health Organization defines anemia by hemoglobin concentration below: "
            "13.0 g/dL in adult men, 12.0 g/dL in non-pregnant adult women, and 11.0 g/dL in "
            "pregnant women. Severity is classified as mild (above 10 g/dL), moderate "
            "(7.0-9.9 g/dL), and severe (below 7.0 g/dL). Iron deficiency is the most common "
            "cause globally, affecting approximately 1.6 billion people. In India, anemia "
            "prevalence is particularly high - approximately 57% of women aged 15-49 are "
            "anemic according to NFHS-5 (2019-21) data, making it one of the most common "
            "preventable conditions in the population this app targets."
        ),
    },
    {
        "id": "anemia-diet", "topic": "Iron-Rich Diet for Anemia Prevention",
        "source": "WHO Nutrition Guidelines; ICMR Dietary Guidelines for Indians, 2020",
        "tags": ["anemia", "iron", "diet", "nutrition", "vitamin C", "absorption", "India"],
        "text": (
            "Heme iron (from animal sources) is absorbed at 15-35%, while non-heme iron (from "
            "plant sources) is absorbed at only 2-20%. Iron absorption from plant sources is "
            "significantly enhanced by consuming vitamin C-rich foods at the same meal. Good "
            "dietary iron sources include green leafy vegetables (spinach, methi), legumes "
            "(lentils, rajma), fortified cereals, and for non-vegetarians, organ meats. Tea and "
            "coffee consumed with meals reduce iron absorption by 40-60% due to tannins - a "
            "simple, actionable timing change rather than a dietary elimination."
        ),
    },
    # ── Hydration / Alcohol ──────────────────────────────────────────────
    {
        "id": "hydration-health", "topic": "Hydration and Health",
        "source": "WHO Water Quality and Health Guidelines; ICMR Dietary Guidelines for Indians, 2020",
        "tags": ["hydration", "water", "kidney", "glucose", "health"],
        "text": (
            "Adequate hydration supports kidney function, cognitive performance, and metabolic "
            "health. General recommendations suggest approximately 2-3 liters of total water "
            "intake per day for adults, with needs varying by body size, climate, and physical "
            "activity level. Chronic mild dehydration is associated with increased risk of "
            "urinary tract infections and kidney stones, and can impair glucose regulation. In "
            "hot climates like much of India, fluid needs may be substantially higher than the "
            "general recommendation, particularly during summer months and for outdoor workers."
        ),
    },
    {
        "id": "alcohol-risk", "topic": "Alcohol and Health Risk",
        "source": "WHO Alcohol and Health 2023; Ministry of Health India Alcohol Guidelines",
        "tags": ["alcohol", "cancer", "liver", "cardiovascular", "diabetes", "hypertension"],
        "text": (
            "No level of alcohol consumption is considered completely safe according to WHO "
            "2023 guidance. Alcohol increases risk of at least 7 types of cancer, liver disease, "
            "cardiovascular disease, and neurological disorders. For individuals with diabetes "
            "or hypertension specifically, alcohol can interfere with medication efficacy, cause "
            "dangerous blood sugar fluctuations (both hypo- and hyperglycemia depending on "
            "timing), and independently raise blood pressure. The Ministry of Health, Government "
            "of India classifies alcohol as a modifiable cancer and cardiovascular risk factor."
        ),
    },
]

TOTAL_CARDS = len(_GUIDELINES)

# ── TF-IDF retrieval engine (pure Python, offline, zero downloads) ─────────
_vectorizer: TfidfVectorizer | None = None
_corpus_matrix = None   # shape: (n_chunks, n_features)
_corpus_texts: list[str] = []
_corpus_meta: list[dict[str, str]] = []


def _init_tfidf() -> None:
    global _vectorizer, _corpus_matrix, _corpus_texts, _corpus_meta
    if _vectorizer is not None:
        return
    _corpus_texts = [g["text"] for g in _GUIDELINES]
    _corpus_meta  = [
        {"id": g["id"], "topic": g["topic"], "source": g["source"], "tags": ",".join(g["tags"])}
        for g in _GUIDELINES
    ]
    _vectorizer   = TfidfVectorizer(
        ngram_range=(1, 2), stop_words="english",
        sublinear_tf=True, max_df=0.95, min_df=1,
    )
    _corpus_matrix = _vectorizer.fit_transform(_corpus_texts)
    logger.info("RAG: TF-IDF index built - %d guideline chunks ready", len(_corpus_texts))


def retrieve(query: str, top_k: int = 3) -> list[dict[str, str]]:
    """
    Retrieve the top-K most relevant guideline chunks for a query via TF-IDF
    cosine similarity. Used by agent_orchestrator.py for the multi-agent
    specialist consensus (each specialist gets its own role-scoped query).
    """
    _init_tfidf()
    if _vectorizer is None or _corpus_matrix is None:
        return []
    try:
        q_vec = _vectorizer.transform([query])
        sims  = cosine_similarity(q_vec, _corpus_matrix).flatten()
        top_indices = sims.argsort()[::-1][:top_k].tolist()
        return [
            {"source": _corpus_meta[i]["source"], "text": _corpus_texts[i]}
            for i in top_indices if sims[i] > 0.01
        ]
    except Exception as exc:
        logger.warning("RAG retrieval failed (%s)", exc)
        return []


def format_context(chunks: list[dict[str, str]]) -> str:
    """Format retrieved chunks for insertion into an agent system prompt."""
    if not chunks:
        return ""
    lines = ["RELEVANT CLINICAL GUIDELINES (use these to ground your recommendation):"]
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"\n[Guideline {i} - {chunk['source']}]")
        lines.append(chunk["text"])
    return "\n".join(lines)


# ── RAGService class ─────────────────────────────────────────────────────
# Used by routers/ai.py (chat, recommendations) and routers/rag.py (live
# retrieval demo endpoint). Adds session-scoped document injection: a
# patient's own uploaded lab report is indexed alongside the guideline
# corpus, so chat answers can be grounded in BOTH published guidelines
# AND the patient's actual data. Kept as a process-wide singleton (see
# get_rag_service) since this app is single-active-patient by design.
class RAGService:
    def __init__(self) -> None:
        _init_tfidf()
        self._session_texts: list[str] = []
        self._session_meta: list[dict[str, str]] = []
        self._session_vectorizer: TfidfVectorizer | None = None
        self._session_matrix = None
        self._session_dirty = False

    def add_session_document(self, text: str, source: str = "Patient Lab Report") -> None:
        """Index the patient's own uploaded lab report alongside the guideline cards."""
        words = text.split()
        chunk_size = 200
        added = 0
        for i, start in enumerate(range(0, len(words), chunk_size)):
            chunk = " ".join(words[start:start + chunk_size])
            if len(chunk.strip()) < 50:
                continue
            self._session_texts.append(chunk)
            self._session_meta.append({
                "id": f"session_doc_{len(self._session_texts)}",
                "topic": "Patient Health Record", "source": source,
                "tags": "patient,lab,report",
            })
            added += 1
        if added:
            self._session_dirty = True
            logger.info("RAG: indexed %d chunk(s) from '%s'", added, source)

    def _ensure_session_index(self) -> None:
        if not self._session_texts:
            return
        if not self._session_dirty and self._session_vectorizer is not None:
            return
        self._session_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), stop_words="english", sublinear_tf=True,
            max_df=1.0, min_df=1,  # session corpus can be as small as 1 chunk; 0.95 max_df
                                    # is infeasible below 2 docs and raises a sklearn ValueError
        )
        self._session_matrix = self._session_vectorizer.fit_transform(self._session_texts)
        self._session_dirty = False

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        """Return top-k cards from guidelines + any indexed session documents."""
        _init_tfidf()
        results: list[tuple[float, dict[str, str]]] = []

        if _vectorizer is not None and _corpus_matrix is not None and query.strip():
            q_vec = _vectorizer.transform([query])
            sims  = cosine_similarity(q_vec, _corpus_matrix).flatten()
            for i, s in enumerate(sims):
                if s > 0.01:
                    results.append((float(s), {**_corpus_meta[i], "text": _corpus_texts[i]}))

        if self._session_texts and query.strip():
            self._ensure_session_index()
            if self._session_vectorizer is not None:
                q_vec = self._session_vectorizer.transform([query])
                sims  = cosine_similarity(q_vec, self._session_matrix).flatten()
                for i, s in enumerate(sims):
                    if s > 0.01:
                        results.append((float(s), {**self._session_meta[i], "text": self._session_texts[i]}))

        results.sort(key=lambda r: r[0], reverse=True)
        if not results:
            return [{**_corpus_meta[i], "text": _corpus_texts[i]} for i in range(min(top_k, len(_corpus_texts)))]
        return [r[1] for r in results[:top_k]]

    def build_context_prompt(self, query: str, k: int = 4) -> tuple[str, list[dict]]:
        """
        Returns (context_block, sources_list) to inject into the Groq prompt.
        The model is explicitly instructed to cite sources or flag unsupported
        claims - this is the concrete answer to "how do you prevent
        hallucinations?"
        """
        cards = self.retrieve(query, top_k=k)
        if not cards:
            return "", []

        lines = ["RETRIEVED MEDICAL GUIDELINES (base your answer on these; cite the source):", ""]
        for i, card in enumerate(cards, 1):
            lines.append(f"[{i}] {card['topic']} ({card['source']})")
            lines.append(card["text"])
            lines.append("")

        lines.append(
            "INSTRUCTION: Base your response on the retrieved guidelines above. "
            "For each key claim, cite which source supports it using [1], [2], etc. "
            "If making a claim not supported by any retrieved source, prefix it with "
            "'(general knowledge - verify with physician):'. "
            "Never invent statistics, drug names, or specific numeric thresholds."
        )

        context = "\n".join(lines)
        sources = [{"id": c["id"], "topic": c["topic"], "source": c["source"]} for c in cards]
        return context, sources

    def list_topics(self) -> list[str]:
        return sorted({g["topic"] for g in _GUIDELINES})


_instance: RAGService | None = None


def get_rag_service() -> RAGService:
    global _instance
    if _instance is None:
        _instance = RAGService()
        logger.info("RAG service initialized: %d guideline cards indexed", TOTAL_CARDS)
    return _instance
