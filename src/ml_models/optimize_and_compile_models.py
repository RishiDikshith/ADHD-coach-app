"""
Unified ML Model Optimization & Production Compilation
=====================================================
Trains all 4 core machine learning models under optimized hyperparameter settings,
applies feature selection, packages them into standard scikit-learn Pipelines, 
and compiles them directly to their production paths with joblib compression (compress=3).
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from catboost import CatBoostRegressor

# Resolve project directories
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))

MODELS_DIR = os.path.join(project_root, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 80)
print("UNIFIED PRODUCTION MODEL COMPILATION ENGINE")
print("=" * 80)

# ============================================================================
# 1. COMPILING MENTAL HEALTH NLP MODEL (8,000 max features, compressed Pipeline)
# ============================================================================
print("\n--- 1/4 COMPILING MENTAL HEALTH NLP MODEL ---")
try:
    df_mh = pd.read_csv(os.path.join(project_root, "data/cleaned/mental_health_cleaned.csv"))
    df_mh = df_mh.dropna(subset=["cleaned_text"])
    df_mh = df_mh[df_mh["cleaned_text"].str.strip() != ""]
    
    X_mh = df_mh["cleaned_text"].tolist()
    y_mh = df_mh["label"].tolist()
    
    tfidf = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )
    
    lr_mh = LogisticRegression(
        C=10.0,
        max_iter=1000,
        solver='lbfgs',
        class_weight='balanced',
        random_state=42
    )
    
    # Bundle into scikit-learn Pipeline
    nlp_pipeline = Pipeline([
        ('vectorizer', tfidf),
        ('classifier', lr_mh)
    ])
    
    print("Fitting NLP pipeline...")
    nlp_pipeline.fit(X_mh, y_mh)
    
    # Save production file (compressed)
    prod_nlp_path = os.path.join(MODELS_DIR, "mental_health_nlp_pipeline.pkl")
    joblib.dump(nlp_pipeline, prod_nlp_path, compress=3)
    print(f"[SUCCESS] Saved production pipeline: {prod_nlp_path} | Size: {os.path.getsize(prod_nlp_path)/1024:.2f} KB")
    
    # Save final tuple version for test/evaluation compatibility
    final_nlp_path = os.path.join(MODELS_DIR, "mental_health_nlp_final.pkl")
    joblib.dump((lr_mh, tfidf), final_nlp_path, compress=3)
    print(f"[SUCCESS] Saved evaluation final tuple: {final_nlp_path}")
    
except Exception as e:
    print(f"[ERROR] Failed to compile NLP Model: {e}")


# ============================================================================
# 2. COMPILING BEHAVIORAL PRODUCTIVITY MODEL (15 features, CatBoost Regressor)
# ============================================================================
print("\n--- 2/4 COMPILING BEHAVIORAL PRODUCTIVITY MODEL ---")
try:
    df_prod = pd.read_csv(os.path.join(project_root, "data/featured/behavioral_scaled.csv"))
    
    top_features = [
        'study_hours_per_day', 'phone_usage_hours', 'health_productivity', 'sleep_hours', 
        'break_efficiency', 'screen_study_ratio', 'exercise_minutes', 'youtube_hours', 
        'study_sleep_ratio', 'gaming_hours', 'caffeine_stress', 'social_media_hours', 
        'coffee_intake_mg', 'age', 'stress_level'
    ]
    
    X_prod = df_prod[top_features]
    y_prod = np.log1p(df_prod["productivity_score"])
    
    cat_model = CatBoostRegressor(
        iterations=800,
        learning_rate=0.03,
        depth=7,
        l2_leaf_reg=2,
        verbose=0,
        random_state=42
    )
    
    print("Fitting CatBoost model on top 15 features...")
    cat_model.fit(X_prod, y_prod)
    
    # Save production file (compressed regressor directly)
    prod_cb_path = os.path.join(MODELS_DIR, "productivity_model.pkl")
    joblib.dump(cat_model, prod_cb_path, compress=3)
    print(f"[SUCCESS] Saved production model: {prod_cb_path} | Size: {os.path.getsize(prod_cb_path)/1024:.2f} KB")
    
    # Save final tuple for compatibility
    final_cb_path = os.path.join(MODELS_DIR, "productivity_model_final.pkl")
    joblib.dump((cat_model, top_features), final_cb_path, compress=3)
    print(f"[SUCCESS] Saved evaluation final tuple: {final_cb_path}")
    
except Exception as e:
    print(f"[ERROR] Failed to compile Productivity Model: {e}")


# ============================================================================
# 3. COMPILING STUDENT DEPRESSION MODEL (SMOTE + Logistic Regression)
# ============================================================================
print("\n--- 3/4 COMPILING STUDENT DEPRESSION MODEL ---")
try:
    df_stud = pd.read_csv(os.path.join(project_root, "data/featured/student_scaled.csv"))
    target_stud = "Do you have Depression?"
    
    X_stud = df_stud.drop(target_stud, axis=1)
    y_stud = df_stud[target_stud]
    
    # Pipeline matching optimal grid-search parameters
    stud_pipeline = ImbPipeline([
        ('smote', SMOTE(random_state=42, k_neighbors=3)),
        ('model', LogisticRegression(
            C=0.1,
            class_weight='balanced',
            solver='liblinear',
            max_iter=1000,
            random_state=42
        ))
    ])
    
    print("Fitting SMOTE Student Depression pipeline...")
    stud_pipeline.fit(X_stud, y_stud)
    
    # Save production file (compressed pipeline directly)
    prod_stud_path = os.path.join(MODELS_DIR, "student_model.pkl")
    joblib.dump(stud_pipeline, prod_stud_path, compress=3)
    print(f"[SUCCESS] Saved production model: {prod_stud_path} | Size: {os.path.getsize(prod_stud_path)/1024:.2f} KB")
    
    # Save final dictionary for compatibility
    final_stud_path = os.path.join(MODELS_DIR, "student_model_final.pkl")
    joblib.dump({"model": stud_pipeline, "threshold": 0.50}, final_stud_path, compress=3)
    print(f"[SUCCESS] Saved evaluation final dict: {final_stud_path}")
    
except Exception as e:
    print(f"[ERROR] Failed to compile Student Model: {e}")


# ============================================================================
# 4. COMPILING ADHD RISK CLASSIFIER (Stacked Logistic Pipeline)
# ============================================================================
print("\n--- 4/4 COMPILING ADHD RISK CLASSIFIER ---")
try:
    df_adhd = pd.read_csv(os.path.join(project_root, "data/cleaned/adhd_cleaned.csv"))
    
    # Derived target variable
    threshold_adhd = df_adhd["asrs_total"].median()
    df_adhd["adhd_risk"] = (df_adhd["asrs_total"] > threshold_adhd).astype(int)
    y_adhd = df_adhd["adhd_risk"]
    
    # Compute dynamic dynamic features using the newly fit models
    print("Generating nlp_risk dynamic feature...")
    text_col = "cleaned_text" if "cleaned_text" in df_adhd.columns else "if_yes_please_list_these_difficulties_and_or_symptoms"
    text_data = df_adhd[text_col].fillna("")
    df_adhd["nlp_risk"] = nlp_pipeline.predict_proba(text_data)[:, 1]
    
    print("Generating productivity_score dynamic feature...")
    prod_input = pd.DataFrame()
    for col in top_features:
        prod_input[col] = df_adhd[col] if col in df_adhd.columns else 0.0
    df_adhd["productivity_score"] = cat_model.predict(prod_input[top_features])
    
    features_adhd = [
        "nlp_risk", "productivity_score", "age", "sex", "home_language", 
        "psy1004_grade", "nbt_ave", "nbt_math", "nbt_al", "matric_mark"
    ]
    
    # Strict fallback for missing values
    for f in features_adhd:
        if f not in df_adhd.columns:
            if f == "home_language":
                df_adhd[f] = "unknown"
            else:
                df_adhd[f] = 0.0
                
    X_adhd = df_adhd[features_adhd]
    
    from sklearn.impute import SimpleImputer
    
    num_cols = X_adhd.select_dtypes(include=["int64", "float64"]).columns
    cat_cols = X_adhd.select_dtypes(include=["object"]).columns
    
    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
            ("scaler", StandardScaler())
        ]), num_cols),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ]), cat_cols)
    ])
    
    adhd_pipeline = Pipeline([
        ("pre", preprocessor),
        ("clf", LogisticRegression(
            max_iter=500,
            class_weight="balanced",
            random_state=42
        ))
    ])
    
    print("Fitting ADHD Risk Stacked pipeline...")
    adhd_pipeline.fit(X_adhd, y_adhd)
    
    # Save production file (compressed pipeline)
    prod_adhd_path = os.path.join(MODELS_DIR, "adhd_risk_model.pkl")
    joblib.dump(adhd_pipeline, prod_adhd_path, compress=3)
    print(f"[SUCCESS] Saved production pipeline: {prod_adhd_path} | Size: {os.path.getsize(prod_adhd_path)/1024:.2f} KB")
    
    # Save final for compatibility
    final_adhd_path = os.path.join(MODELS_DIR, "adhd_risk_model_final.pkl")
    joblib.dump(adhd_pipeline, final_adhd_path, compress=3)
    print(f"[SUCCESS] Saved evaluation final pipeline: {final_adhd_path}")
    
except Exception as e:
    print(f"[ERROR] Failed to compile ADHD Model: {e}")

print("\n" + "=" * 80)
print("ALL MODELS TRAINING AND PRODUCTION COMPILATION COMPLETED!")
print("=" * 80)
