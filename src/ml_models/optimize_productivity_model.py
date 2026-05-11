import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.ensemble import VotingRegressor

from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

print("="*70)
print("PRODUCTIVITY MODEL - FINAL FAST VERSION")
print("="*70)

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/featured/behavioral_scaled.csv")

X = df.drop("productivity_score", axis=1)
y = np.log1p(df["productivity_score"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

# =========================
# FEATURE IMPORTANCE
# =========================
print("\n--- Feature Importance ---")

quick_cb = CatBoostRegressor(iterations=200, verbose=0, random_state=42)
quick_cb.fit(X_train, y_train)

importance = pd.DataFrame({
    "feature": X.columns,
    "importance": quick_cb.get_feature_importance()
}).sort_values("importance", ascending=False)

top_features = importance.head(15)["feature"].tolist()

X_train = X_train[top_features]
X_test = X_test[top_features]

print("Top features selected:", top_features)

# =========================
# MODELS (NO GRIDSEARCH)
# =========================

print("\n--- Training Models ---")

# CatBoost (BEST)
cat_model = CatBoostRegressor(
    iterations=800,
    learning_rate=0.03,
    depth=7,
    l2_leaf_reg=2,
    verbose=0,
    random_state=42
)
cat_model.fit(X_train, y_train)

# XGBoost (optional)
xgb_model = XGBRegressor(
    n_estimators=600,
    learning_rate=0.03,
    max_depth=7,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1,
    tree_method='hist'
)
xgb_model.fit(X_train, y_train)

# LightGBM (optional)
lgb_model = LGBMRegressor(
    n_estimators=600,
    learning_rate=0.03,
    max_depth=7,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
lgb_model.fit(X_train, y_train)

# =========================
# ENSEMBLE (OPTIONAL)
# =========================
print("\n--- Creating Ensemble ---")

ensemble = VotingRegressor([
    ('cat', cat_model),
    ('xgb', xgb_model),
    ('lgb', lgb_model)
])

ensemble.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================

def evaluate(name, model):
    pred_log = model.predict(X_test)

    r2_log = r2_score(y_test, pred_log)
    mae_log = mean_absolute_error(y_test, pred_log)

    pred_orig = np.expm1(pred_log)
    y_orig = np.expm1(y_test)

    r2_orig = r2_score(y_orig, pred_orig)
    mae_orig = mean_absolute_error(y_orig, pred_orig)

    print(f"\n{name}:")
    print(f"  Log R2: {r2_log:.4f}")
    print(f"  Original R2: {r2_orig:.4f}")
    print(f"  MAE: {mae_orig:.4f}")

print("\n" + "="*70)
print("MODEL PERFORMANCE")
print("="*70)

evaluate("CatBoost", cat_model)
evaluate("XGBoost", xgb_model)
evaluate("LightGBM", lgb_model)
evaluate("Ensemble", ensemble)

# =========================
# CROSS VALIDATION
# =========================

print("\n--- Cross Validation (CatBoost) ---")

cv_scores = cross_val_score(cat_model, X_train, y_train, cv=5, scoring='r2')
print(f"CV R2: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

# =========================
# SAVE BEST MODEL
# =========================

# Use CatBoost (best)
joblib.dump((cat_model, top_features), "models/productivity_model_final.pkl")

print("\n" + "="*70)
print("✓ FINAL MODEL SAVED (CatBoost)")
print("="*70)