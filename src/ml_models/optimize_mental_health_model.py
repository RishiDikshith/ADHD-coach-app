import os
import joblib
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold

print("="*70)
print("MENTAL HEALTH NLP MODEL - FINAL FAST VERSION")
print("="*70)

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/cleaned/mental_health_cleaned.csv")
df = df.dropna(subset=["cleaned_text"])
df = df[df["cleaned_text"].str.strip() != ""]

print(f"Dataset shape: {df.shape}")
print(f"Class distribution:\n{df['label'].value_counts()}\n")

X = df["cleaned_text"].tolist()
y = df["label"].tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# =========================
# TF-IDF (OPTIMIZED)
# =========================
print("\n--- TF-IDF Vectorization ---")

tfidf = TfidfVectorizer(
    max_features=15000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

print(f"TF-IDF shape: {X_train_tfidf.shape}")

# =========================
# LOGISTIC REGRESSION (BEST MODEL)
# =========================
print("\n--- Training Logistic Regression ---")

lr = LogisticRegression(
    C=10.0,
    max_iter=1000,
    solver='lbfgs',
    class_weight='balanced',
    random_state=42
)

lr.fit(X_train_tfidf, y_train)

# =========================
# FAST SVM (LINEAR + CALIBRATION)
# =========================
print("\n--- Training Fast Linear SVM ---")

svm_base = LinearSVC(class_weight='balanced', max_iter=2000)
svm = CalibratedClassifierCV(svm_base)

svm.fit(X_train_tfidf, y_train)

# =========================
# ENSEMBLE (OPTIONAL)
# =========================
print("\n--- Creating Ensemble ---")

ensemble = VotingClassifier(
    estimators=[
        ('lr', lr),
        ('svm', svm),
    ],
    voting='soft'
)

ensemble.fit(X_train_tfidf, y_train)

# =========================
# EVALUATION FUNCTION
# =========================
def evaluate(name, model):
    y_pred = model.predict(X_test_tfidf)
    y_prob = model.predict_proba(X_test_tfidf)[:, 1]

    print(f"\n{name}:")
    print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"  F1 Score:  {f1_score(y_test, y_pred):.4f}")
    print(f"  ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}")

# =========================
# RESULTS
# =========================
print("\n" + "="*70)
print("MODEL PERFORMANCE")
print("="*70)

evaluate("Logistic Regression", lr)
evaluate("Linear SVM", svm)
evaluate("Ensemble", ensemble)

# =========================
# SAVE BEST MODEL
# =========================

# Usually Logistic Regression wins
joblib.dump((lr, tfidf), "models/mental_health_nlp_final.pkl")

print("\n" + "="*70)
print("✓ FINAL NLP MODEL SAVED (Logistic Regression)")
print("="*70)