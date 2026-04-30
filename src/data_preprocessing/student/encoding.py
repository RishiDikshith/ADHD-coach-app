import pandas as pd
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv("data/cleaned/student_data.csv")

le = LabelEncoder()

for col in df.columns:
    if df[col].dtype == "object":
        df[col] = le.fit_transform(df[col].astype(str))

df.to_csv("data/processed/student_encoded.csv", index=False)

print("Encoding completed")