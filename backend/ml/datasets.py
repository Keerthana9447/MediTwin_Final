"""
MediTwin AI — ML Dataset Loaders
═══════════════════════════════════════════════════════════════
Loading priority for each dataset, in order:
  1. Local file at backend/ml/data/{name}.csv (you downloaded it yourself)
  2. Auto-download from a documented stable public mirror (Diabetes,
     Heart Disease only — see DATA_SOURCES below)
  3. Offline statistical fallback — NOT the real dataset. A generator
     that samples from the PUBLISHED summary statistics (means, std
     devs, class balance) of the real dataset, with labels generated
     via a genuine logistic relationship to the features (not random
     noise) so a model trained on it learns real, non-trivial
     structure and produces a meaningful (if approximate) ROC-AUC.
     This keeps the system fully functional offline/at a hackathon
     venue with dead wifi, while being completely honest that mode
     3 is a statistical approximation, not the original data.

Every loader returns (X: pd.DataFrame, y: pd.Series, meta: dict) where
meta["source"] is one of "local_file" / "downloaded" / "offline_fallback"
— this provenance is surfaced all the way to the frontend so nobody
can mistake fallback-mode numbers for genuine Kaggle/UCI benchmark
results.

═══════════════════════════════════════════════════════════════
DATA_SOURCES — exact public datasets this module is designed for
═══════════════════════════════════════════════════════════════
  • Diabetes  : Pima Indians Diabetes Database (768 rows, 8 features)
                Stable mirror: raw.githubusercontent.com/jbrownlee/Datasets
                Also on Kaggle: "uciml/pima-indians-diabetes-database"
  • Heart     : UCI Heart Disease (Cleveland subset, 303 rows, 13 features)
                Official: archive.ics.uci.edu/dataset/45/heart+disease
                Also on Kaggle: "redwankarimsony/heart-disease-data"
  • Stroke    : Stroke Prediction Dataset (Kaggle, ~5110 rows, 10 features)
                Kaggle: "fedesoriano/stroke-prediction-dataset" (CC0)
                No auto-download wired here — Kaggle requires an
                authenticated API call (kaggle.json credentials), so
                this loader expects YOU to download it once via the
                Kaggle UI/CLI and place it at backend/ml/data/stroke.csv
                (see ml/data/README.md for exact steps).
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("meditwin.ml.datasets")
DATA_DIR = Path(__file__).parent / "data"

DIABETES_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome",
]

HEART_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]

STROKE_NUMERIC_COLS = ["age", "avg_glucose_level", "bmi"]
STROKE_BINARY_COLS = ["hypertension", "heart_disease"]
STROKE_CATEGORICAL_COLS = ["gender", "ever_married", "work_type", "Residence_type", "smoking_status"]

# ── Candidate download mirrors (tried in order, short timeout, never blocks startup) ──
DIABETES_URLS = [
    "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
]
HEART_URLS = [
    "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
]


def _try_download(urls: list[str], timeout: float = 4.0) -> str | None:
    """Try each URL briefly; return raw text on first success, else None. Never raises."""
    try:
        import httpx
    except ImportError:
        return None
    for url in urls:
        try:
            resp = httpx.get(url, timeout=timeout, follow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 100:
                logger.info("Downloaded dataset from %s", url)
                return resp.text
        except Exception as exc:
            logger.info("Download attempt failed (%s): %s", url, exc)
    return None


def _label_from_quantile(prob: np.ndarray, target_rate: float, rng: np.random.RandomState, jitter: float = 0.03) -> np.ndarray:
    """
    Convert a continuous risk score into a binary label whose overall positive
    rate matches a documented real-world class balance (e.g. Pima's ~34.9%,
    Cleveland's ~46%, Kaggle Stroke's ~4.9%) by thresholding at the matching
    quantile of the score distribution, with light per-sample jitter so the
    cutoff isn't a perfectly deterministic line (keeps it learnable but not
    trivially separable). Preserves rank order, so high-risk feature
    combinations are still much more likely to be labeled positive.
    """
    threshold = np.quantile(prob, 1.0 - target_rate)
    noisy_prob = prob + rng.normal(0, jitter, size=prob.shape)
    return (noisy_prob > threshold).astype(int)


# ═══════════════════════════════════════════════════════════
#  DIABETES — Pima Indians Diabetes Database
# ═══════════════════════════════════════════════════════════
def _diabetes_fallback(n: int = 768, seed: int = 42) -> pd.DataFrame:
    """
    Statistical approximation of the Pima Indians Diabetes Database.
    Sampled from the dataset's PUBLISHED summary statistics (commonly
    cited means/stds from the original UCI/Kaggle distribution), with
    the Outcome label generated via a genuine logistic combination of
    Glucose + BMI + Age + DiabetesPedigreeFunction — a real learnable
    relationship, not independent random noise.
    """
    rng = np.random.RandomState(seed)
    preg    = np.clip(rng.normal(3.85, 3.37, n), 0, 17).round()
    glucose = np.clip(rng.normal(120.9, 32.0, n), 44, 199)
    bp      = np.clip(rng.normal(69.1, 19.4, n), 24, 122)
    skin    = np.clip(rng.normal(20.5, 16.0, n), 0, 99)
    insulin = np.clip(rng.gamma(2.0, 60, n), 0, 846)
    bmi     = np.clip(rng.normal(32.0, 7.88, n), 18, 67)
    dpf     = np.clip(rng.gamma(2.0, 0.23, n), 0.08, 2.42)
    age     = np.clip(rng.normal(33.2, 11.76, n), 21, 81).round()

    z = (
        0.035 * (glucose - 120) + 0.09 * (bmi - 32) +
        0.04 * (age - 33) + 1.1 * (dpf - 0.47) +
        rng.normal(0, 0.9, n)
    )
    prob = 1 / (1 + np.exp(-z))
    outcome = _label_from_quantile(prob, target_rate=0.349, rng=rng)  # real Pima positive rate ≈ 34.9%

    return pd.DataFrame({
        "Pregnancies": preg, "Glucose": glucose, "BloodPressure": bp,
        "SkinThickness": skin, "Insulin": insulin, "BMI": bmi,
        "DiabetesPedigreeFunction": dpf, "Age": age, "Outcome": outcome,
    })


def load_diabetes_data() -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    local = DATA_DIR / "diabetes.csv"
    if local.exists():
        df = pd.read_csv(local)
        if list(df.columns) != DIABETES_COLUMNS and df.shape[1] == len(DIABETES_COLUMNS):
            df.columns = DIABETES_COLUMNS
        source = "local_file"
    else:
        text = _try_download(DIABETES_URLS)
        if text:
            from io import StringIO
            df = pd.read_csv(StringIO(text), header=None, names=DIABETES_COLUMNS)
            source = "downloaded"
        else:
            df = _diabetes_fallback()
            source = "offline_fallback"

    # Known data-quality nuance: zeros in these columns are missing-value placeholders,
    # not physiologically real measurements — impute with column median.
    for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        df[col] = df[col].replace(0, np.nan)
        df[col] = df[col].fillna(df[col].median())

    X = df.drop(columns=["Outcome"])
    y = df["Outcome"].astype(int)
    meta = {
        "disease": "Diabetes", "n_samples": len(df), "n_features": X.shape[1],
        "positive_rate": round(float(y.mean()), 3), "source": source,
        "dataset_name": "Pima Indians Diabetes Database",
    }
    return X, y, meta


# ═══════════════════════════════════════════════════════════
#  HEART DISEASE — UCI Cleveland subset
# ═══════════════════════════════════════════════════════════
def _heart_fallback(n: int = 303, seed: int = 42) -> pd.DataFrame:
    """
    Statistical approximation of the UCI Heart Disease (Cleveland) dataset.
    Sampled from published summary statistics; target generated via a
    genuine logistic combination of age + trestbps + chol + thalach +
    exang + oldpeak — mirroring the actual clinical risk drivers this
    dataset is known for, not independent random noise.
    """
    rng = np.random.RandomState(seed)
    age      = np.clip(rng.normal(54.4, 9.0, n), 29, 77).round()
    sex      = rng.binomial(1, 0.68, n)
    cp       = rng.randint(0, 4, n)
    trestbps = np.clip(rng.normal(131.6, 17.5, n), 94, 200)
    chol     = np.clip(rng.normal(246.7, 51.8, n), 126, 564)
    fbs      = rng.binomial(1, 0.15, n)
    restecg  = rng.randint(0, 3, n)
    thalach  = np.clip(rng.normal(149.6, 22.9, n), 71, 202)
    exang    = rng.binomial(1, 0.33, n)
    oldpeak  = np.clip(rng.gamma(1.5, 0.7, n), 0, 6.2)
    slope    = rng.randint(0, 3, n)
    ca       = rng.choice([0, 1, 2, 3], n, p=[0.58, 0.21, 0.13, 0.08])
    thal     = rng.choice([3, 6, 7], n, p=[0.55, 0.07, 0.38])

    z = (
        0.04 * (age - 54) + 0.55 * sex + 0.30 * cp +
        0.02 * (trestbps - 131) + 0.004 * (chol - 247) +
        -0.025 * (thalach - 150) + 0.9 * exang + 0.45 * oldpeak +
        0.35 * ca + rng.normal(0, 0.9, n)
    )
    prob = 1 / (1 + np.exp(-z))
    target = _label_from_quantile(prob, target_rate=0.46, rng=rng)  # real Cleveland (binarized) ≈ 46%

    return pd.DataFrame({
        "age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol,
        "fbs": fbs, "restecg": restecg, "thalach": thalach, "exang": exang,
        "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal, "target": target,
    })


def load_heart_data() -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    local = DATA_DIR / "heart.csv"
    if local.exists():
        df = pd.read_csv(local)
        source = "local_file"
        if "target" not in df.columns and "num" in df.columns:
            df = df.rename(columns={"num": "target"})
    else:
        text = _try_download(HEART_URLS)
        if text:
            from io import StringIO
            df = pd.read_csv(StringIO(text), header=None, names=HEART_COLUMNS, na_values="?")
            source = "downloaded"
        else:
            df = _heart_fallback()
            source = "offline_fallback"

    # UCI raw file uses "?" for missing ca/thal — impute with column median/mode
    for col in ["ca", "thal"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    # Original UCI target is severity 0-4; binarize to presence/absence of disease
    df["target"] = (pd.to_numeric(df["target"], errors="coerce").fillna(0) > 0).astype(int)

    X = df.drop(columns=["target"])
    y = df["target"].astype(int)
    meta = {
        "disease": "Heart Disease", "n_samples": len(df), "n_features": X.shape[1],
        "positive_rate": round(float(y.mean()), 3), "source": source,
        "dataset_name": "UCI Heart Disease (Cleveland)",
    }
    return X, y, meta


# ═══════════════════════════════════════════════════════════
#  STROKE — Kaggle Stroke Prediction Dataset
# ═══════════════════════════════════════════════════════════
def _stroke_fallback(n: int = 5110, seed: int = 42) -> pd.DataFrame:
    """
    Statistical approximation of the Kaggle Stroke Prediction Dataset.
    Matches the real dataset's heavy class imbalance (~4.9% positive)
    and its known top risk drivers (age, hypertension, heart_disease,
    avg_glucose_level) via a genuine logistic relationship.
    """
    rng = np.random.RandomState(seed)
    age = np.clip(rng.gamma(4.0, 11, n), 0.1, 82)
    gender = rng.choice(["Male", "Female"], n, p=[0.41, 0.59])
    hypertension = rng.binomial(1, 0.095, n)
    heart_disease = rng.binomial(1, 0.054, n)
    ever_married = rng.choice(["Yes", "No"], n, p=[0.65, 0.35])
    work_type = rng.choice(
        ["Private", "Self-employed", "Govt_job", "children", "Never_worked"],
        n, p=[0.57, 0.16, 0.13, 0.13, 0.01],
    )
    residence = rng.choice(["Urban", "Rural"], n, p=[0.51, 0.49])
    avg_glucose = np.clip(rng.gamma(3.0, 35, n) + 55, 55, 271)
    bmi = np.clip(rng.normal(28.9, 7.85, n), 10, 92)
    smoking = rng.choice(
        ["never smoked", "formerly smoked", "smokes", "Unknown"],
        n, p=[0.37, 0.17, 0.15, 0.31],
    )

    z = (
        0.06 * (age - 43) + 1.3 * hypertension + 1.4 * heart_disease +
        0.012 * (avg_glucose - 106) + 0.02 * (bmi - 29) +
        rng.normal(0, 1.1, n)
    )
    prob = 1 / (1 + np.exp(-z))
    stroke = _label_from_quantile(prob, target_rate=0.0487, rng=rng, jitter=0.02)  # real Kaggle stroke rate ≈ 4.87%

    return pd.DataFrame({
        "gender": gender, "age": age, "hypertension": hypertension,
        "heart_disease": heart_disease, "ever_married": ever_married,
        "work_type": work_type, "Residence_type": residence,
        "avg_glucose_level": avg_glucose, "bmi": bmi, "smoking_status": smoking,
        "stroke": stroke,
    })


def load_stroke_data() -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    local = DATA_DIR / "stroke.csv"
    if local.exists():
        df = pd.read_csv(local)
        if "id" in df.columns:
            df = df.drop(columns=["id"])
        source = "local_file"
    else:
        # No auto-download for Stroke — Kaggle requires authenticated API access.
        # See ml/data/README.md for one-time manual download instructions.
        df = _stroke_fallback()
        source = "offline_fallback"

    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    X = df.drop(columns=["stroke"])
    y = df["stroke"].astype(int)

    # One-hot encode categoricals — keep a record of the exact column order for inference
    X = pd.get_dummies(X, columns=[c for c in STROKE_CATEGORICAL_COLS if c in X.columns], drop_first=False)

    meta = {
        "disease": "Stroke", "n_samples": len(df), "n_features": X.shape[1],
        "positive_rate": round(float(y.mean()), 3), "source": source,
        "dataset_name": "Stroke Prediction Dataset (Kaggle, fedesoriano)",
    }
    return X, y, meta


LOADERS = {
    "diabetes": load_diabetes_data,
    "heart": load_heart_data,
    "stroke": load_stroke_data,
}
