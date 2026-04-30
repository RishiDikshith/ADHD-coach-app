import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import numpy as np

from src.utils.helpers import align_features_to_model, prepare_model_for_inference


ADHD_EXCLUDE_COLS = [
    "asrs_total",
    "bai1_total",
    "bdi1_total",
    "psy1004_grade",
    "nbt_completed",
    "nbt_year",
    "nbt_al",
    "nbt_math",
    "nbt_ql",
    "nbt_ave",
    "nbt_did_math",
    "nbt_alql_ave",
    "matric_mark",
    "aas_change",
]

ADHD_LEAKAGE_PROXY_COLS = {
    "have_you_ever_been_diagnosed_with_a_mental_illness",
    "was_this_diagnosis_made_before_or_after_you_left_high_school",
    "if_you_have_been_diagnosed_with_a_mental_illness_at_what_age_was_this",
}


def build_adhd_regression_frame(df):
    df = df.dropna(subset=["asrs_total"]).copy()
    feature_cols = [
        col
        for col in df.columns
        if col not in ADHD_EXCLUDE_COLS
        and col not in ADHD_LEAKAGE_PROXY_COLS
        and "asrs" not in col.lower()
        and "bai1" not in col.lower()
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
        numeric_hint = pd.to_numeric(
            values.str.lower().str.extract(r"(\d+(?:\.\d+)?)", expand=False),
            errors="coerce",
        )

        if (nunique > 50 or unique_ratio > 0.20) and numeric_hint.notna().mean() >= 0.35:
            numeric_hint_col = f"{col}_numeric_hint"
            df[numeric_hint_col] = numeric_hint
            prepared_features.append(numeric_hint_col)

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


def evaluate_classification_model(model_path, X_test, y_test, model_name):
    model = prepare_model_for_inference(joblib.load(model_path))
    X_test = align_features_to_model(X_test, model)

    y_pred = model.predict(X_test)

    print(f"\n=== {model_name} Evaluation ===")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Precision:", precision_score(y_test, y_pred, average='weighted'))
    print("Recall:", recall_score(y_test, y_pred, average='weighted'))
    print("F1 Score:", f1_score(y_test, y_pred, average='weighted'))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

def evaluate_regression_model(model_path, X_test, y_test, model_name):
    model = prepare_model_for_inference(joblib.load(model_path))
    X_test = align_features_to_model(X_test, model)

    y_pred = model.predict(X_test)

    # Reverse log transformation for the productivity model
    if model_name == "Productivity":
        y_pred = np.expm1(y_pred)

    print(f"\n=== {model_name} Evaluation ===")
    print("R2 Score:", r2_score(y_test, y_pred))
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("MSE:", mean_squared_error(y_test, y_pred))
    print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))

if __name__ == "__main__":
    # Load test data
    print("Loading test data...")

    # Mental Health
    mh_df = pd.read_csv("data/cleaned/mental_health_cleaned.csv")
    mh_df = mh_df.dropna(subset=["cleaned_text"])
    mh_df = mh_df[mh_df["cleaned_text"].str.strip() != ""]
    X_mh = mh_df["cleaned_text"]
    y_mh = mh_df["label"]
    _, X_mh_test, _, y_mh_test = train_test_split(X_mh, y_mh, test_size=0.2, random_state=42)

    # Productivity
    bh_df = pd.read_csv("data/featured/behavioral_scaled.csv")
    X_prod = bh_df.drop(["productivity_score"], axis=1, errors="ignore")
    y_prod = bh_df["productivity_score"]
    _, X_prod_test, _, y_prod_test = train_test_split(X_prod, y_prod, test_size=0.2, random_state=42)

    # Student
    stud_df = pd.read_csv("data/featured/student_scaled.csv")
    target = "Do you have Depression?"
    X_stud = stud_df.drop(target, axis=1)
    y_stud = stud_df[target]
    _, X_stud_test, _, y_stud_test = train_test_split(X_stud, y_stud, test_size=0.2, random_state=42, stratify=y_stud)

    # ADHD (from ADHD data)
    adhd_df = pd.read_csv("data/cleaned/adhd_cleaned.csv")
    X_adhd, y_adhd = build_adhd_regression_frame(adhd_df)
    _, X_adhd_test, _, y_adhd_test = train_test_split(X_adhd, y_adhd, test_size=0.2, random_state=42)

    # Evaluate models
    evaluate_classification_model("models/mental_health_nlp_pipeline.pkl", X_mh_test, y_mh_test, "Mental Health NLP")
    evaluate_regression_model("models/productivity_model.pkl", X_prod_test, y_prod_test, "Productivity")
    evaluate_classification_model("models/student_model.pkl", X_stud_test, y_stud_test, "Student Depression")
    evaluate_regression_model("models/adhd_model.pkl", X_adhd_test, y_adhd_test, "ADHD Score")

    print("\nEvaluation complete!")
