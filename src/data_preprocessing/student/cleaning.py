import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/Student Mental health.csv")

print("Original Shape:", df.shape)

# Handle missing values
for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].fillna(df[col].mode()[0])
    else:
        df[col] = df[col].fillna(df[col].median())

# Remove outliers
numeric_cols = df.select_dtypes(include=np.number).columns

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df[col] >= Q1 - 1.5 * IQR) &
            (df[col] <= Q3 + 1.5 * IQR)]

print("Shape after cleaning:", df.shape)

df.to_csv("data/cleaned/student_data.csv", index=False)

print("Student data cleaned")