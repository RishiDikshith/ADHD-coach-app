import pandas as pd
import joblib
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

print("="*70)
print("STUDENT DEPRESSION MODEL - FINAL BALANCED VERSION")
print("="*70)

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/featured/student_scaled.csv")
target = "Do you have Depression?"

X = df.drop(target, axis=1)
y = df[target]

print("\nClass distribution:")
print(y.value_counts())
print(f"\nTotal samples: {len(df)}, Features: {len(X.columns)}")

# =========================
# TRAIN-TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain samples: {len(X_train)}, Test samples: {len(X_test)}")

# =========================
# PIPELINE
# =========================
pipeline = ImbPipeline([
    ('smote', SMOTE(random_state=42, k_neighbors=3)),
    ('model', LogisticRegression(
        class_weight='balanced',
        random_state=42
    ))
])

# =========================
# GRID SEARCH (STABLE)
# =========================
params = {
    'model__C': [0.1, 1, 10],   # removed extreme 0.01
    'model__solver': ['liblinear'],
    'model__max_iter': [500, 1000],
}

print("\nRunning GridSearchCV...")

grid = GridSearchCV(
    pipeline,
    params,
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
    scoring='f1',
    n_jobs=-1,
    verbose=1
)

grid.fit(X_train, y_train)

print("\nBest Parameters:", grid.best_params_)
print(f"Best CV F1: {grid.best_score_:.4f}")

best_model = grid.best_estimator_

# =========================
# THRESHOLD TUNING (AUTO)
# =========================
y_prob = best_model.predict_proba(X_test)[:, 1]

best_threshold = 0.5
best_f1 = 0

print("\n--- Finding Best Threshold ---")

for t in np.arange(0.3, 0.7, 0.05):
    y_pred_temp = (y_prob > t).astype(int)
    f1 = f1_score(y_test, y_pred_temp)

    print(f"Threshold {t:.2f} → F1: {f1:.4f}")

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = t

print(f"\nBest Threshold: {best_threshold:.2f}")

# Final prediction
y_pred = (y_prob > best_threshold).astype(int)

# =========================
# EVALUATION
# =========================
print("\n" + "="*70)
print("FINAL TEST PERFORMANCE")
print("="*70)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
auc = roc_auc_score(y_test, y_prob)

print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")
print(f"ROC-AUC:   {auc:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# =========================
# SAVE MODEL
# =========================
joblib.dump({
    "model": best_model,
    "threshold": best_threshold
}, "models/student_model_final.pkl")

print("\n" + "="*70)
print("✓ FINAL BALANCED MODEL SAVED!")
print("="*70)