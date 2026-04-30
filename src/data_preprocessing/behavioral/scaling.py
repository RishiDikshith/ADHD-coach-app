import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

df = pd.read_csv("data/featured/behavioral_final.csv")

X = df.drop("productivity_score", axis=1)
y = df["productivity_score"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
X_scaled["productivity_score"] = y

X_scaled.to_csv("data/featured/behavioral_scaled.csv", index=False)

joblib.dump(scaler, "models/behavioral_scaler.pkl")

print("Scaling completed")