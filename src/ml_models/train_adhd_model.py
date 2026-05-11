# train_adhd_model.py

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

print("="*70)
print("FINAL ADHD STACKED MODEL (REAL + STABLE)")
print("="*70)

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/cleaned/adhd_cleaned.csv")

# =========================
# TARGET
# =========================
threshold = df["asrs_total"].median()
df["adhd_risk"] = (df["asrs_total"] > threshold).astype(int)
y = df["adhd_risk"]

# =========================
# LOAD MODELS
# =========================
nlp_model, tfidf = joblib.load("models/mental_health_nlp_final.pkl")
prod_model, prod_features = joblib.load("models/productivity_model_final.pkl")

print("✓ Models loaded")

# =========================
# BUILD META FEATURES
# =========================
meta_features = []

for _, row in df.iterrows():

    # -------- NLP (text proxy) --------
    text = str(row.get(
        "if_yes_please_list_these_difficulties_and_or_symptoms", ""
    ))
    X_text = tfidf.transform([text])
    nlp_score = nlp_model.predict_proba(X_text)[:, 1][0]

    # -------- PRODUCTIVITY --------
    prod_input = np.array([
        row.get(f, 0) for f in prod_features
    ]).reshape(1, -1)
    prod_score = prod_model.predict(prod_input)[0]

    # -------- DEMOGRAPHIC --------
    age = row["age"]

    sex = row["sex"]
    if isinstance(sex, str):
        sex = 1 if sex.lower() == "male" else 0

    # -------- DERIVED FEATURES (SAFE, NON-LEAKY) --------
    focus_proxy = row.get("psy1004_grade", 0) / 100
    cognitive_load = row.get("nbt_ave", 0) / 100
    academic_stress = abs(row.get("matric_mark", 0) - row.get("nbt_ave", 0)) / 100

    # -------- FINAL FEATURE VECTOR --------
    meta_features.append([
        nlp_score,
        prod_score,
        age,
        sex,
        focus_proxy,
        cognitive_load,
        academic_stress
    ])

X_meta = np.array(meta_features)

print(f"Feature shape: {X_meta.shape}")

# =========================
# SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X_meta, y, test_size=0.2, stratify=y, random_state=42
)

# =========================
# META MODEL
# =========================
model = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    ))
])

# =========================
# TRAIN
# =========================
model.fit(X_train, y_train)

# =========================
# EVALUATE
# =========================
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\n=== PERFORMANCE ===")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("F1:", f1_score(y_test, y_pred))
print("AUC:", roc_auc_score(y_test, y_prob))

# =========================
# CROSS VALIDATION
# =========================
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_meta, y, cv=cv, scoring="roc_auc")

print("\nCV AUC:", cv_scores.mean(), "+/-", cv_scores.std()*2)

# =========================
# SAVE
# =========================
joblib.dump({
    "model": model
}, "models/adhd_stacked_model_final.pkl")

print("\n✓ FINAL STACKED MODEL SAVED")