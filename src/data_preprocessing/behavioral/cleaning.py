import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/behavioral_data.csv")

# Drop ID
if "student_id" in df.columns:
    df = df.drop("student_id", axis=1)

# Encode gender
df["gender"] = df["gender"].map({
    "Male": 0,
    "Female": 1,
    "Other": 2
})

# -------------------------
# Handle Missing Values
# -------------------------
print("\nMissing Values Before:")
print(df.isnull().sum())

# Fill numeric columns with median
numeric_cols = df.select_dtypes(include=np.number).columns
for col in numeric_cols:
    df[col] = df[col].fillna(df[col].median())

# Fill categorical with mode
categorical_cols = df.select_dtypes(include="object").columns
for col in categorical_cols:
    df[col] = df[col].fillna(df[col].mode()[0])

print("\nMissing Values After:")
print(df.isnull().sum())

# Remove outliers using IQR
for col in df.select_dtypes(include=np.number).columns:
    if col != "productivity_score":
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

print("Shape after outlier removal:", df.shape)

# Save cleaned data
df.to_csv("data/cleaned/behavioral_data.csv", index=False)

print("\nBehavioral data cleaned and saved!")
