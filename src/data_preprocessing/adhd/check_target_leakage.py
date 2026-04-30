import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/adhd_final.csv")

target = "asrs_total"

# Keep only numeric columns
numeric_df = df.select_dtypes(include=np.number)

corr = numeric_df.corr()[target].sort_values(ascending=False)

print("Correlation with Target:")
print(corr)