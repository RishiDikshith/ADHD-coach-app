import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/student_encoded.csv")

corr = df.corr().abs()

upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

high_corr = [column for column in upper.columns if any(upper[column] > 0.9)]

print("Dropping highly correlated:", high_corr)

df = df.drop(columns=high_corr)

df.to_csv("data/processed/student_corr_filtered.csv", index=False)

print("Correlation filtering done")