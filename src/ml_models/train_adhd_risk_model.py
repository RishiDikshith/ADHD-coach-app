import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

df = pd.read_csv("data/featured/behavioral_scaled.csv")

# Create ADHD Risk Score
df["adhd_risk_score"] = (
    df["phone_usage_hours"]
    + df["social_media_hours"]
    + df["youtube_hours"]
    + df["gaming_hours"]
    + df["stress_level"]
    + df["caffeine_stress"]
    - df["sleep_hours"]
    - df["exercise_minutes"] / 60
    - df["study_hours_per_day"]
    - df["break_efficiency"]
    - df["health_productivity"]
)

target = "adhd_risk_score"

# 🚨 FIXING DATA LEAKAGE: 
# The target 'adhd_risk_score' was calculated directly from these features.
# If we don't drop them, the model just memorizes the formula and overfits perfectly.
leakage_features = [
    "phone_usage_hours", "social_media_hours", "youtube_hours",
    "gaming_hours", "stress_level", "caffeine_stress",
    "sleep_hours", "exercise_minutes", "study_hours_per_day",
    "break_efficiency", "health_productivity"
]

# Remove productivity score, target, and all constituent leakage features
cols_to_drop = [target, "productivity_score"] + [col for col in leakage_features if col in df.columns]
X = df.drop(columns=cols_to_drop)
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Use CatBoost with early stopping and regularization to prevent overfitting
model = CatBoostRegressor(
    iterations=1000, 
    learning_rate=0.05, 
    depth=6, 
    l2_leaf_reg=5, 
    verbose=100, 
    random_state=42
)

model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=50)

print("Train R2:", model.score(X_train, y_train))
print("Test R2:", model.score(X_test, y_test))
print("MAE:", mean_absolute_error(y_test, model.predict(X_test)))
print("R2 Score:", r2_score(y_test, model.predict(X_test)))

joblib.dump(model, "models/adhd_risk_model.pkl")

print("\nFinal ADHD Risk Model Saved!")