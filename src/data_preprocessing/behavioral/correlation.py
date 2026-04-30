from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("data/featured/behavioral_data.csv")

# Correlation matrix
corr = df.corr(numeric_only=True)

plt.figure(figsize=(12,8))
sns.heatmap(corr, cmap="coolwarm")
plt.title("Correlation Matrix")
output_dir = Path("results")
output_dir.mkdir(exist_ok=True)
plot_path = output_dir / "behavioral_correlation_heatmap.png"
plt.tight_layout()
plt.savefig(plot_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"Correlation heatmap saved to {plot_path}")

# Remove highly correlated features
corr_abs = corr.abs()
upper = corr_abs.where(np.triu(np.ones(corr_abs.shape), k=1).astype(bool))

to_drop = [column for column in upper.columns if any(upper[column] > 0.90)]

print("Highly correlated features:", to_drop)

df = df.drop(columns=to_drop)

df.to_csv("data/featured/behavioral_corr_selected.csv", index=False)

print("Correlation filtering done")
