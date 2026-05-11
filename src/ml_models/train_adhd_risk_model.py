# train_adhd_risk_model.py

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

print("="*70)
print("FINAL ADHD MODEL (FULLY FIXED)")
print("="*70)

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/cleaned/adhd_cleaned.csv")

# =========================
# CREATE TARGET
# =========================
if "adhd_risk" not in df.columns:
    if "asrs_total" in df.columns:
        threshold = df["asrs_total"].median()
        df["adhd_risk"] = (df["asrs_total"] > threshold).astype(int)
        print("✓ Target created from asrs_total")
    else:
        raise ValueError("❌ Missing 'asrs_total' column")

y = df["adhd_risk"]

# =========================
# LOAD MODELS
# =========================
print("\nLoading models...")

nlp_available = False
prod_available = False

# NLP
try:
    nlp_bundle = joblib.load("models/mental_health_nlp_final.pkl")

    if isinstance(nlp_bundle, tuple):
        nlp_model, tfidf = nlp_bundle
    else:
        nlp_model = nlp_bundle["model"]
        tfidf = nlp_bundle["vectorizer"]

    nlp_available = True
    print("✓ NLP model loaded")

except Exception as e:
    print("⚠️ NLP not available:", str(e))

# Productivity
try:
    prod_bundle = joblib.load("models/productivity_model_final.pkl")

    if isinstance(prod_bundle, tuple):
        prod_model, prod_features = prod_bundle
    else:
        prod_model = prod_bundle["model"]
        prod_features = prod_bundle["features"]

    prod_available = True
    print("✓ Productivity model loaded")

except Exception as e:
    print("⚠️ Productivity not available:", str(e))

# =========================
# NLP FEATURE
# =========================
if nlp_available:
    text_col = None
    for col in ["cleaned_text", "text", "response"]:
        if col in df.columns:
            text_col = col
            break

    if text_col:
        text_data = df[text_col].fillna("")
        X_text = tfidf.transform(text_data)
        df["nlp_risk"] = nlp_model.predict_proba(X_text)[:, 1]
        print("✓ NLP feature added")
    else:
        df["nlp_risk"] = 0.5
        print("⚠️ No text column → default NLP")
else:
    df["nlp_risk"] = 0.5

# =========================
# PRODUCTIVITY FEATURE (FIXED)
# =========================
if prod_available:
    try:
        prod_input = pd.DataFrame()

        for col in prod_features:
            if col in df.columns:
                prod_input[col] = df[col]
            else:
                prod_input[col] = 0

        prod_input = prod_input[prod_features]

        df["productivity_score"] = prod_model.predict(prod_input)
        print("✓ Productivity feature added")

    except Exception as e:
        print("⚠️ Productivity failed:", str(e))
        df["productivity_score"] = 0.5
else:
    df["productivity_score"] = 0.5

# =========================
# FINAL FEATURES
# =========================
features = [
    "nlp_risk",
    "productivity_score",
    "age",
    "sex",
    "home_language",
    "psy1004_grade",
    "nbt_ave",
    "nbt_math",
    "nbt_al",
    "matric_mark"
]

features = [f for f in features if f in df.columns]

print("\nUsing features:", features)

X = df[features]

# =========================
# PREPROCESSING
# =========================
num_cols = X.select_dtypes(include=["int64", "float64"]).columns
cat_cols = X.select_dtypes(include=["object"]).columns

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
])

# =========================
# MODEL
# =========================
model = Pipeline([
    ("pre", preprocessor),
    ("clf", LogisticRegression(
        max_iter=500,
        class_weight="balanced"
    ))
])

# =========================
# TRAIN TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

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
cv_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")

print("\nCV AUC:", cv_scores.mean(), "+/-", cv_scores.std()*2)

# =========================
# SAVE MODEL
# =========================
joblib.dump(model, "models/adhd_risk_model_final.pkl")

print("\n✓ FINAL MODEL SAVED")
print("="*70)