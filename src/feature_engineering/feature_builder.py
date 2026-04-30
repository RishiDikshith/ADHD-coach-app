import pandas as pd
import numpy as np

def build_features(df):
    """
    Enhanced feature engineering for ADHD productivity assessment.
    Creates domain-specific features for better model performance.
    
    Args:
        df: pandas DataFrame or dict with user data
        
    Returns:
        pandas DataFrame with engineered features
    """
    
    # Convert dict to DataFrame if needed
    if isinstance(df, dict):
        df = pd.DataFrame([df])
    elif not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected dict or DataFrame, got {type(df)}")

    # ✅ Ensure all required base columns exist
    required_cols = [
        "study_hours_per_day",
        "sleep_hours",
        "phone_usage_hours",
        "social_media_hours",
        "youtube_hours",
        "gaming_hours",
        "breaks_per_day",
        "coffee_intake_mg",
        "exercise_minutes",
        "stress_level",
        "age",
        "gender",
        "task_completion_rate",
        "mood_log_score"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    # ---------------- ADVANCED FEATURE ENGINEERING ----------------

    # 1️⃣ Study Efficiency Metrics
    df["study_sleep_ratio"] = df["study_hours_per_day"] / (df["sleep_hours"] + 1)
    df["study_intensity"] = df["study_hours_per_day"] / (df["breaks_per_day"] + 1)
    df["study_productivity"] = df["study_hours_per_day"] * (1 / (df["stress_level"] + 1))

    # 2️⃣ Screen Time & Digital Habits
    df["total_screen_time"] = (
        df["phone_usage_hours"] +
        df["social_media_hours"] +
        df["youtube_hours"] +
        df["gaming_hours"]
    )
    df["screen_study_ratio"] = df["total_screen_time"] / (df["study_hours_per_day"] + 1)
    df["digital_distraction_index"] = df["total_screen_time"] / (df["sleep_hours"] + 1)

    # 3️⃣ Health & Wellness Features
    df["health_score"] = (
        df["sleep_hours"] +
        df["exercise_minutes"] / 60
    )
    df["health_productivity"] = df["health_score"] / (df["stress_level"] + 1)
    df["caffeine_stress"] = df["coffee_intake_mg"] * df["stress_level"]
    df["caffeine_efficiency"] = df["coffee_intake_mg"] / (df["sleep_hours"] + 1)

    # 4️⃣ Break & Recovery Features
    df["break_efficiency"] = df["breaks_per_day"] / (df["study_hours_per_day"] + 1)
    df["recovery_ratio"] = df["sleep_hours"] / (df["total_screen_time"] + 1)

    # 5️⃣ Age & Demographic Interactions
    df["age_stress_factor"] = df["age"] * df["stress_level"]
    df["gender_productivity"] = df["gender"] * df["study_hours_per_day"]

    # 5.5️⃣ Advanced Tracking Ideas
    df["task_completion_efficiency"] = df["task_completion_rate"] / (df["breaks_per_day"] + 1)
    df["mood_stress_ratio"] = df["mood_log_score"] / (df["stress_level"] + 1)

    # 6️⃣ Composite Risk Scores
    df["adhd_risk_screen"] = (
        df["phone_usage_hours"] +
        df["social_media_hours"] +
        df["youtube_hours"] +
        df["gaming_hours"]
    ) / (df["study_hours_per_day"] + 1)

    df["adhd_risk_health"] = (
        df["stress_level"] +
        df["caffeine_stress"]
    ) / (df["sleep_hours"] + df["exercise_minutes"]/60 + 1)

    # 7️⃣ Polynomial Features (for non-linear relationships)
    df["stress_squared"] = df["stress_level"] ** 2
    df["screen_log"] = np.log(df["total_screen_time"] + 1)

    # 8️⃣ Interaction Features
    df["stress_x_screen"] = df["stress_level"] * df["total_screen_time"]
    df["health_x_study"] = df["health_score"] * df["study_hours_per_day"]

    # Handle any infinite or NaN values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(df.median(numeric_only=True))

    return df