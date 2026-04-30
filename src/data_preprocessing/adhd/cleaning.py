import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("data/raw/adhd_screening_data.csv", encoding="latin1")

print("Original Shape:", df.shape)

# -------------------------------
# Fix Target Column
# -------------------------------
if "asrs1_total.y" in df.columns:
    df.rename(columns={"asrs1_total.y": "asrs_total"}, inplace=True)

if "asrs1_total.x" in df.columns:
    df.drop(columns=["asrs1_total.x"], inplace=True)

# Remove unnamed columns
df = df.loc[:, ~df.columns.str.contains("Unnamed")]

# -------------------------------
# Handle Missing Values
# -------------------------------
for col in df.select_dtypes(include=np.number).columns:
    df[col] = df[col].fillna(df[col].median())

for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].fillna("Unknown")

print("Target Exists:", "asrs_total" in df.columns)

df.to_csv("data/cleaned/adhd_cleaned.csv", index=False)

print("ADHD cleaned data saved")