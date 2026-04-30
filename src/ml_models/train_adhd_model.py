import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split


RANDOM_STATE = 42
TARGET = "asrs_total"
HIGH_CORRELATION_THRESHOLD = 0.8
HIGH_CARDINALITY_UNIQUES = 50
HIGH_CARDINALITY_RATIO = 0.20
NUMERIC_HINT_MIN_RATIO = 0.35
FEATURE_COUNTS_TO_TRY = (4, 6, 8, 10, 12)
EFFICIENCY_TOLERANCE = 0.01
ABLATION_IMPROVEMENT_THRESHOLD = 0.03
MIN_FEATURES_TO_KEEP = 4

EXCLUDE_COLS = [
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

LEAKAGE_PROXY_COLS = {
    "have_you_ever_been_diagnosed_with_a_mental_illness",
    "was_this_diagnosis_made_before_or_after_you_left_high_school",
    "if_you_have_been_diagnosed_with_a_mental_illness_at_what_age_was_this",
}

MODEL_PARAMS = {
    "iterations": 220,
    "learning_rate": 0.05,
    "depth": 3,
    "l2_leaf_reg": 9,
    "min_data_in_leaf": 8,
    "bootstrap_type": "Bernoulli",
    "subsample": 0.8,
    "loss_function": "RMSE",
    "verbose": 0,
    "random_state": RANDOM_STATE,
    "thread_count": -1,
}


def make_model(iterations=None):
    params = dict(MODEL_PARAMS)
    if iterations is not None:
        params["iterations"] = iterations
    return CatBoostRegressor(**params)


def extract_base_feature_columns(df):
    feature_cols = [
        col
        for col in df.columns
        if col not in EXCLUDE_COLS
        and col not in LEAKAGE_PROXY_COLS
        and "asrs" not in col.lower()
        and "bai1" not in col.lower()
        and "bdi1" not in col.lower()
    ]
    if LEAKAGE_PROXY_COLS:
        print("\nDropped leakage-prone diagnosis proxy features:")
        print(sorted(LEAKAGE_PROXY_COLS))
    return feature_cols


def add_numeric_hints_and_drop_text_noise(df, feature_cols):
    working_df = df.copy()
    filtered_features = []
    dropped_high_cardinality = []
    numeric_hint_features = []

    for col in feature_cols:
        if working_df[col].dtype != "object":
            filtered_features.append(col)
            continue

        values = working_df[col].fillna("Unknown").astype(str).str.strip()
        nunique = values.nunique()
        unique_ratio = nunique / len(working_df)
        numeric_hint = pd.to_numeric(
            values.str.lower().str.extract(r"(\d+(?:\.\d+)?)", expand=False),
            errors="coerce",
        )
        numeric_hint_ratio = numeric_hint.notna().mean()

        if (
            (nunique > HIGH_CARDINALITY_UNIQUES or unique_ratio > HIGH_CARDINALITY_RATIO)
            and numeric_hint_ratio >= NUMERIC_HINT_MIN_RATIO
        ):
            numeric_hint_col = f"{col}_numeric_hint"
            working_df[numeric_hint_col] = numeric_hint
            numeric_hint_features.append(numeric_hint_col)
            filtered_features.append(numeric_hint_col)

        if nunique > HIGH_CARDINALITY_UNIQUES and unique_ratio > HIGH_CARDINALITY_RATIO:
            dropped_high_cardinality.append(col)
            continue

        filtered_features.append(col)

    if numeric_hint_features:
        print("\nAdded numeric hint features from semi-structured text:")
        print(numeric_hint_features)

    if dropped_high_cardinality:
        print("\nDropped high-cardinality categorical features:")
        print(dropped_high_cardinality)

    return working_df, filtered_features


def remove_hidden_leakage(df, feature_cols):
    numeric_feature_cols = [
        col for col in feature_cols if pd.api.types.is_numeric_dtype(df[col])
    ]
    correlations = df[numeric_feature_cols].corrwith(df[TARGET]).abs().sort_values(ascending=False)
    leaky_features = correlations[correlations > HIGH_CORRELATION_THRESHOLD].index.tolist()
    filtered_feature_cols = [col for col in feature_cols if col not in leaky_features]
    return filtered_feature_cols, correlations, leaky_features


def prepare_model_frame(df, feature_cols):
    X = df[feature_cols].copy()
    cat_features = [col for col in feature_cols if X[col].dtype == "object"]

    if cat_features:
        X[cat_features] = X[cat_features].fillna("Unknown").astype(str)

    return X, cat_features


def fit_model(X_train, y_train, X_valid, y_valid, cat_features):
    model = make_model()
    model.fit(
        X_train,
        y_train,
        eval_set=(X_valid, y_valid),
        early_stopping_rounds=40,
        use_best_model=True,
        cat_features=cat_features or None,
        verbose=0,
    )
    return model


def evaluate_subset(feature_subset, X_train, y_train, X_valid, y_valid, cat_features):
    subset_cat = [col for col in feature_subset if col in cat_features]
    model = fit_model(
        X_train[feature_subset],
        y_train,
        X_valid[feature_subset],
        y_valid,
        subset_cat,
    )
    predictions = model.predict(X_valid[feature_subset])
    return model, r2_score(y_valid, predictions)


def run_cv(X, y, feature_subset, cat_features, n_splits=5):
    subset_cat = [col for col in feature_subset if col in cat_features]
    folds = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    scores = []

    for train_idx, valid_idx in folds.split(X):
        X_train_fold = X.iloc[train_idx][feature_subset]
        X_valid_fold = X.iloc[valid_idx][feature_subset]
        y_train_fold = y.iloc[train_idx]
        y_valid_fold = y.iloc[valid_idx]

        fold_model = fit_model(
            X_train_fold,
            y_train_fold,
            X_valid_fold,
            y_valid_fold,
            subset_cat,
        )
        fold_pred = fold_model.predict(X_valid_fold)
        scores.append(r2_score(y_valid_fold, fold_pred))

    return np.array(scores)


def select_efficient_subset(ranked_features, X_train, y_train, X_valid, y_valid, cat_features):
    candidate_sizes = sorted(
        {
            size
            for size in FEATURE_COUNTS_TO_TRY
            if size <= len(ranked_features)
        }
    )
    if not candidate_sizes:
        candidate_sizes = [len(ranked_features)]

    subset_results = []
    print("\n--- Searching for the Smallest Strong Feature Set ---")
    for size in candidate_sizes:
        candidate_subset = ranked_features[:size]
        _, valid_r2 = evaluate_subset(
            candidate_subset,
            X_train,
            y_train,
            X_valid,
            y_valid,
            cat_features,
        )
        subset_results.append({"size": size, "features": candidate_subset, "valid_r2": valid_r2})
        print(f"Top {size:>2} features -> Validation R2: {valid_r2:.4f}")

    best_valid_r2 = max(result["valid_r2"] for result in subset_results)
    shortlisted = [
        result for result in subset_results
        if result["valid_r2"] >= best_valid_r2 - EFFICIENCY_TOLERANCE
    ]
    chosen_result = min(shortlisted, key=lambda result: (result["size"], -result["valid_r2"]))

    print(
        f"\nSelected top {chosen_result['size']} features "
        f"(best validation R2 = {best_valid_r2:.4f}, efficiency tolerance = {EFFICIENCY_TOLERANCE:.3f})"
    )

    return chosen_result["features"], best_valid_r2


def prune_features_by_ablation(selected_features, X_train, y_train, X_valid, y_valid, cat_features):
    current_features = list(selected_features)
    _, baseline_r2 = evaluate_subset(
        current_features,
        X_train,
        y_train,
        X_valid,
        y_valid,
        cat_features,
    )

    print(
        "\n--- Pruning Features That Hurt Validation Performance "
        f"(threshold = {ABLATION_IMPROVEMENT_THRESHOLD:.3f}) ---"
    )

    while len(current_features) > MIN_FEATURES_TO_KEEP:
        improvements = []

        for feature in current_features:
            candidate_features = [col for col in current_features if col != feature]
            _, candidate_r2 = evaluate_subset(
                candidate_features,
                X_train,
                y_train,
                X_valid,
                y_valid,
                cat_features,
            )
            delta = candidate_r2 - baseline_r2
            direction = "improved" if delta > 0 else "dropped"
            print(
                f"Without '{feature}': Validation R2 = {candidate_r2:.4f} "
                f"(Performance {direction} by {abs(delta):.4f})"
            )
            improvements.append((feature, delta, candidate_features, candidate_r2))

        best_feature, best_delta, best_subset, best_r2 = max(improvements, key=lambda item: item[1])
        if best_delta < ABLATION_IMPROVEMENT_THRESHOLD:
            print("\nNo more features cleared the pruning threshold.")
            break

        print(
            f"\nDropping '{best_feature}' because validation R2 improved by {best_delta:.4f}."
        )
        current_features = best_subset
        baseline_r2 = best_r2

    return current_features, baseline_r2


def final_fit_and_report(
    feature_subset,
    X_train_val,
    y_train_val,
    X_test,
    y_test,
    cat_features,
    best_iteration,
):
    subset_cat = [col for col in feature_subset if col in cat_features]
    final_iterations = max(
        50,
        best_iteration + 1 if best_iteration is not None else MODEL_PARAMS["iterations"],
    )

    final_model = make_model(iterations=final_iterations)
    final_model.fit(
        X_train_val[feature_subset],
        y_train_val,
        cat_features=subset_cat or None,
        verbose=0,
    )

    train_pred = final_model.predict(X_train_val[feature_subset])
    test_pred = final_model.predict(X_test[feature_subset])
    cv_scores = run_cv(
        pd.concat([X_train_val, X_test], axis=0),
        pd.concat([y_train_val, y_test], axis=0),
        feature_subset,
        cat_features,
    )

    print("\n--- Final Lean ADHD Model ---")
    print(f"Final feature count: {len(feature_subset)}")
    print("Selected features:", feature_subset)
    print(f"Final training iterations: {final_iterations}")
    print(f"Efficient CV R2: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    print("Train R2:", r2_score(y_train_val, train_pred))
    print("Test R2:", r2_score(y_test, test_pred))
    print("Train MAE:", mean_absolute_error(y_train_val, train_pred))
    print("Test MAE:", mean_absolute_error(y_test, test_pred))
    print("Train RMSE:", np.sqrt(mean_squared_error(y_train_val, train_pred)))
    print("Test RMSE:", np.sqrt(mean_squared_error(y_test, test_pred)))

    return final_model


df = pd.read_csv("data/cleaned/adhd_cleaned.csv")
df = df.dropna(subset=[TARGET]).copy()

feature_cols = extract_base_feature_columns(df)
df, feature_cols = add_numeric_hints_and_drop_text_noise(df, feature_cols)
feature_cols, correlations, leaky_features = remove_hidden_leakage(df, feature_cols)

if leaky_features:
    print(f"Warning: dropped hidden leaky features (correlation > {HIGH_CORRELATION_THRESHOLD}): {leaky_features}")

print("\nTop 5 highest correlated features (watch these for potential leakage):")
print(correlations.head(5))

X, cat_features = prepare_model_frame(df, feature_cols)
y = df[TARGET]

print("Features:", len(feature_cols))
print("Target: asrs_total")

X_train_val, X_test, y_train_val, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=RANDOM_STATE,
)
X_train, X_valid, y_train, y_valid = train_test_split(
    X_train_val,
    y_train_val,
    test_size=0.25,
    random_state=RANDOM_STATE,
)

baseline_model = fit_model(X_train, y_train, X_valid, y_valid, cat_features)
feature_importances = pd.Series(
    baseline_model.get_feature_importance(),
    index=X.columns,
).sort_values(ascending=False)

print("\nTop 10 Most Important Features:")
print(feature_importances.head(10))

ranked_features = feature_importances.head(max(FEATURE_COUNTS_TO_TRY)).index.tolist()
selected_features, _ = select_efficient_subset(
    ranked_features,
    X_train,
    y_train,
    X_valid,
    y_valid,
    cat_features,
)
selected_features, final_valid_r2 = prune_features_by_ablation(
    selected_features,
    X_train,
    y_train,
    X_valid,
    y_valid,
    cat_features,
)

print(f"\nFinal validation R2 after pruning: {final_valid_r2:.4f}")
selected_model, _ = evaluate_subset(
    selected_features,
    X_train,
    y_train,
    X_valid,
    y_valid,
    cat_features,
)

efficient_model = final_fit_and_report(
    selected_features,
    X_train_val,
    y_train_val,
    X_test,
    y_test,
    cat_features,
    selected_model.get_best_iteration(),
)

joblib.dump(efficient_model, "models/adhd_model.pkl")
print("\nEfficient ADHD model saved!")
