import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

df = pd.read_csv("data/featured/behavioral_data.csv")

# Remove infinite values
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

X = df.drop("productivity_score", axis=1)

vif_data = pd.DataFrame()
vif_data["Feature"] = X.columns
vif_data["VIF"] = [
    variance_inflation_factor(X.values, i)
    for i in range(X.shape[1])
]

print(vif_data.sort_values(by="VIF", ascending=False))

# Drop only derived multicollinear features
drop_cols = [
    "total_screen_time",
    "stress_load",
    "work_life_balance"
]

for col in drop_cols:
    if col in df.columns:
        df = df.drop(col, axis=1)

df.to_csv("data/featured/behavioral_vif_selected.csv", index=False)

print("VIF filtering done")