import pandas as pd
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data/processed/student_corr_filtered.csv")

target = "Do you have Depression?"

X = df.drop(target, axis=1)
y = df[target]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
X_scaled[target] = y

X_scaled.to_csv("data/featured/student_scaled.csv", index=False)

print("Scaling completed")