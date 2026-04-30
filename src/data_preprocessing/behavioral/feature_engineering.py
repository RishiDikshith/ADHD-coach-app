import pandas as pd

df = pd.read_csv("data/cleaned/behavioral_data.csv")

# Screen time
df["total_screen_time"] = (
    df["social_media_hours"] +
    df["youtube_hours"] +
    df["gaming_hours"]
)

# Health score
df["health_score"] = (
    df["sleep_hours"] +
    df["exercise_minutes"] / 60
)

# Study efficiency
df["study_efficiency"] = (
    df["assignments_completed"] /
    (df["study_hours_per_day"] + 0.1)
)

# Stress load
df["stress_load"] = (
    df["stress_level"] /
    (df["sleep_hours"] + 0.1)
)

# Work life balance
df["work_life_balance"] = (
    df["study_hours_per_day"] /
    (df["total_screen_time"] + df["study_hours_per_day"] + 0.1)
)

# New powerful features
df["study_sleep_ratio"] = df["study_hours_per_day"] / (df["sleep_hours"] + 0.1)
df["screen_study_ratio"] = df["total_screen_time"] / (df["study_hours_per_day"] + 0.1)
df["health_productivity"] = df["health_score"] / (df["stress_level"] + 1)
df["caffeine_stress"] = df["coffee_intake_mg"] * df["stress_level"]
df["break_efficiency"] = df["breaks_per_day"] / (df["study_hours_per_day"] + 0.1)

df.to_csv("data/featured/behavioral_data.csv", index=False)

print("Feature engineering completed")