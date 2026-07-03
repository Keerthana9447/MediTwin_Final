# ML Training Data

Place the real public datasets here for full-accuracy production training.
If a file is missing, `train_models.py` automatically falls back to either
a live download (Diabetes, Heart) or a clearly-labeled offline statistical
approximation (Stroke) — the system always works, but accuracy/metrics
will be more representative of the real benchmark with the real files.

## diabetes.csv — Pima Indians Diabetes Database
Auto-downloads by default from a stable GitHub mirror. To use the original
Kaggle copy instead:
1. https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database
2. Download `diabetes.csv`, place it here as `backend/ml/data/diabetes.csv`
Columns expected: Pregnancies, Glucose, BloodPressure, SkinThickness,
Insulin, BMI, DiabetesPedigreeFunction, Age, Outcome

## heart.csv — UCI Heart Disease (Cleveland)
Auto-downloads by default from the UCI archive. To use a Kaggle mirror instead:
1. https://www.kaggle.com/datasets/redwankarimsony/heart-disease-data
2. Download, place here as `backend/ml/data/heart.csv`
Columns expected: age, sex, cp, trestbps, chol, fbs, restecg, thalach,
exang, oldpeak, slope, ca, thal, target (or "num", auto-renamed)

## stroke.csv — Stroke Prediction Dataset (Kaggle)
No auto-download (Kaggle requires authentication). One-time manual step:
1. https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset
2. Download `healthcare-dataset-stroke-data.csv`
3. Rename to `stroke.csv`, place here as `backend/ml/data/stroke.csv`
Columns expected: gender, age, hypertension, heart_disease, ever_married,
work_type, Residence_type, avg_glucose_level, bmi, smoking_status, stroke

---
After placing any of these files, re-run:
```
python train_models.py
```
to retrain on the real data. The Model Lab page will show `"source": "local_file"`
once it's using your real CSV instead of the offline fallback.
