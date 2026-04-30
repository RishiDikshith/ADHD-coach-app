import pandas as pd
from sklearn.ensemble import RandomForestRegressor

df = pd.read_csv("data/featured/behavioral_vif_selected.csv")

# Remove unwanted columns manually
drop_cols = [
    "focus_score",
    "final_grade",
    "attendance_percentage",
    "assignments_completed",
    "health_score",
    "study_efficiency"
]

for col in drop_cols:
    if col in df.columns:
        df = df.drop(col, axis=1)

# Feature importance
X = df.drop("productivity_score", axis=1)
y = df["productivity_score"]

model = RandomForestRegressor()
model.fit(X, y)

importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": model.feature_importances_
}).sort_values(by="Importance", ascending=False)

print("\nFeature Importance:")
print(importance)

df.to_csv("data/featured/behavioral_final.csv", index=False)

print("Final feature selection completed")