"""
Comprehensive Model Evaluation and Comparison
Compares original vs optimized models across all tasks
"""

import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

ADHD_EXCLUDE_COLS = [
    "asrs_total", "bai1_total", "bdi1_total", "psy1004_grade",
    "nbt_completed", "nbt_year", "nbt_al", "nbt_math", "nbt_ql",
    "nbt_ave", "nbt_did_math", "nbt_alql_ave", "matric_mark", "aas_change",
]

ADHD_LEAKAGE_PROXY_COLS = {
    "was_this_diagnosis_made_before_or_after_you_left_high_school",
    "if_you_have_been_diagnosed_with_a_mental_illness_at_what_age_was_this",
}


def build_adhd_regression_frame(df):
    df = df.dropna(subset=["asrs_total"]).copy()
    feature_cols = [
        col for col in df.columns
        if col not in ADHD_EXCLUDE_COLS and col not in ADHD_LEAKAGE_PROXY_COLS
        and "asrs" not in col.lower() and "bai1" not in col.lower()
        and "bdi1" not in col.lower()
    ]

    prepared_features = []
    for col in feature_cols:
        if df[col].dtype != "object":
            prepared_features.append(col)
            continue

        values = df[col].fillna("Unknown").astype(str).str.strip()
        nunique = values.nunique()
        unique_ratio = nunique / len(df)

        if nunique > 50 and unique_ratio > 0.20:
            continue

        prepared_features.append(col)

    numeric_feature_cols = [
        col for col in prepared_features if pd.api.types.is_numeric_dtype(df[col])
    ]
    correlations = df[numeric_feature_cols].corrwith(df["asrs_total"]).abs()
    leaky_features = correlations[correlations > 0.8].index.tolist()
    prepared_features = [col for col in prepared_features if col not in leaky_features]

    X = df[prepared_features].copy()
    cat_cols = [col for col in prepared_features if X[col].dtype == "object"]
    if cat_cols:
        X[cat_cols] = X[cat_cols].fillna("Unknown").astype(str)

    y = df["asrs_total"]
    return X, y


def evaluate_model(y_true, y_pred, model_type='classification', model_name='Model'):
    """Generic evaluation function"""
    results = {'Model': model_name}
    
    if model_type == 'classification':
        results['Accuracy'] = accuracy_score(y_true, y_pred)
        results['Precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        results['Recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        results['F1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    else:  # regression
        results['R²'] = r2_score(y_true, y_pred)
        results['MAE'] = mean_absolute_error(y_true, y_pred)
        results['RMSE'] = np.sqrt(mean_squared_error(y_true, y_pred))
    
    return results


print("="*80)
print("COMPREHENSIVE MODEL EVALUATION - ORIGINAL VS OPTIMIZED")
print("="*80)

evaluation_results = []

# =============================================================================
# 1. MENTAL HEALTH NLP MODEL
# =============================================================================
print("\n" + "="*80)
print("1. MENTAL HEALTH NLP MODEL")
print("="*80)

try:
    mh_df = pd.read_csv("data/cleaned/mental_health_cleaned.csv")
    mh_df = mh_df.dropna(subset=["cleaned_text"])
    mh_df = mh_df[mh_df["cleaned_text"].str.strip() != ""]
    X_mh = mh_df["cleaned_text"]
    y_mh = mh_df["label"]
    _, X_mh_test, _, y_mh_test = train_test_split(X_mh, y_mh, test_size=0.2, random_state=42)
    
    # Original Model
    try:
        with open("models/mental_health_nlp_pipeline.pkl", 'rb') as f:
            orig_model = joblib.load("models/mental_health_nlp_pipeline.pkl")
        y_pred_orig = orig_model.predict(X_mh_test)
        orig_results = evaluate_model(y_mh_test, y_pred_orig, 'classification', 'Mental Health - Original')
        print(f"Original F1: {orig_results['F1']:.4f}")
        evaluation_results.append(orig_results)
    except Exception as e:
        print(f"Error loading original model: {e}")
    
    # Optimized Model
    try:
        opt_model, opt_tfidf = joblib.load("models/mental_health_nlp_optimized.pkl")
        X_mh_test_tfidf = opt_tfidf.transform(X_mh_test)
        y_pred_opt = opt_model.predict(X_mh_test_tfidf)
        opt_results = evaluate_model(y_mh_test, y_pred_opt, 'classification', 'Mental Health - Optimized')
        print(f"Optimized F1: {opt_results['F1']:.4f}")
        evaluation_results.append(opt_results)
    except Exception as e:
        print(f"Error with optimized model: {e}")

except Exception as e:
    print(f"Error in Mental Health evaluation: {e}")

# =============================================================================
# 2. PRODUCTIVITY MODEL
# =============================================================================
print("\n" + "="*80)
print("2. PRODUCTIVITY MODEL")
print("="*80)

try:
    bh_df = pd.read_csv("data/featured/behavioral_scaled.csv")
    X_prod = bh_df.drop(["productivity_score"], axis=1, errors="ignore")
    y_prod = bh_df["productivity_score"]
    _, X_prod_test, _, y_prod_test = train_test_split(X_prod, y_prod, test_size=0.2, random_state=42)
    
    # Original Model
    try:
        orig_model = joblib.load("models/productivity_model.pkl")
        y_pred_orig = orig_model.predict(X_prod_test)
        orig_results = evaluate_model(y_prod_test, y_pred_orig, 'regression', 'Productivity - Original')
        print(f"Original R²: {orig_results['R²']:.4f}")
        evaluation_results.append(orig_results)
    except Exception as e:
        print(f"Error loading original model: {e}")
    
    # Optimized Model
    try:
        opt_model, top_features = joblib.load("models/productivity_model_optimized.pkl")
        X_prod_test_selected = X_prod_test[top_features]
        y_pred_opt = opt_model.predict(X_prod_test_selected)
        opt_results = evaluate_model(y_prod_test, y_pred_opt, 'regression', 'Productivity - Optimized')
        print(f"Optimized R²: {opt_results['R²']:.4f}")
        evaluation_results.append(opt_results)
    except Exception as e:
        print(f"Error with optimized model: {e}")

except Exception as e:
    print(f"Error in Productivity evaluation: {e}")

# =============================================================================
# 3. STUDENT DEPRESSION MODEL
# =============================================================================
print("\n" + "="*80)
print("3. STUDENT DEPRESSION MODEL")
print("="*80)

try:
    stud_df = pd.read_csv("data/featured/student_scaled.csv")
    target = "Do you have Depression?"
    X_stud = stud_df.drop(target, axis=1)
    y_stud = stud_df[target]
    _, X_stud_test, _, y_stud_test = train_test_split(X_stud, y_stud, test_size=0.2, random_state=42, stratify=y_stud)
    
    # Original Model
    try:
        orig_model = joblib.load("models/student_model.pkl")
        y_pred_orig = orig_model.predict(X_stud_test)
        orig_results = evaluate_model(y_stud_test, y_pred_orig, 'classification', 'Student Depression - Original')
        print(f"Original F1: {orig_results['F1']:.4f}")
        evaluation_results.append(orig_results)
    except Exception as e:
        print(f"Error loading original model: {e}")
    
    # Optimized Model
    try:
        opt_model = joblib.load("models/student_model_optimized.pkl")
        y_pred_opt = opt_model.predict(X_stud_test)
        opt_results = evaluate_model(y_stud_test, y_pred_opt, 'classification', 'Student Depression - Optimized')
        print(f"Optimized F1: {opt_results['F1']:.4f}")
        evaluation_results.append(opt_results)
    except Exception as e:
        print(f"Error with optimized model: {e}")

except Exception as e:
    print(f"Error in Student Depression evaluation: {e}")

# =============================================================================
# 4. ADHD SCORE MODEL
# =============================================================================
print("\n" + "="*80)
print("4. ADHD SCORE MODEL")
print("="*80)

try:
    adhd_df = pd.read_csv("data/cleaned/adhd_cleaned.csv")
    X_adhd, y_adhd = build_adhd_regression_frame(adhd_df)
    _, X_adhd_test, _, y_adhd_test = train_test_split(X_adhd, y_adhd, test_size=0.2, random_state=42)
    
    # Original Model
    try:
        orig_model = joblib.load("models/adhd_model.pkl")
        y_pred_orig = orig_model.predict(X_adhd_test)
        orig_results = evaluate_model(y_adhd_test, y_pred_orig, 'regression', 'ADHD Score - Original')
        print(f"Original R²: {orig_results['R²']:.4f}")
        evaluation_results.append(orig_results)
    except Exception as e:
        print(f"Error loading original model: {e}")
    
    # Optimized Model
    try:
        opt_model = joblib.load("models/adhd_model_optimized.pkl")
        y_pred_opt = opt_model.predict(X_adhd_test)
        opt_results = evaluate_model(y_adhd_test, y_pred_opt, 'regression', 'ADHD Score - Optimized')
        print(f"Optimized R²: {opt_results['R²']:.4f}")
        evaluation_results.append(opt_results)
    except Exception as e:
        print(f"Error with optimized model: {e}")

except Exception as e:
    print(f"Error in ADHD evaluation: {e}")

# =============================================================================
# SUMMARY REPORT
# =============================================================================
print("\n" + "="*80)
print("COMPREHENSIVE EVALUATION SUMMARY")
print("="*80)

if evaluation_results:
    results_df = pd.DataFrame(evaluation_results)
    print("\n" + results_df.to_string(index=False))
    
    # Save report
    results_df.to_csv("MODELS_EVALUATION_REPORT.csv", index=False)
    print("\n* Report saved to MODELS_EVALUATION_REPORT.csv")
else:
    print("No evaluation results available")

print("\n" + "="*80)
print("EVALUATION COMPLETE")
print("="*80)
