import pandas as pd

df = pd.read_csv("data/cleaned/adhd_cleaned.csv")

target = "asrs_total"

# Encode sex column
df["sex"] = df["sex"].map({
    "male": 0,
    "female": 1,
    "Male": 0,
    "Female": 1
})

# Convert nbt_completed to numeric
df["nbt_completed"] = df["nbt_completed"].map({
    "Yes": 1,
    "No": 0,
    "yes": 1,
    "no": 0
})

keep_columns = [
    "age",
    "sex",
    "nbt_al",
    "nbt_math",
    "nbt_ql",
    "matric_mark",
    "nbt_year",
    "nbt_completed",
    target
]

df = df[keep_columns]

# Drop any remaining non-numeric rows
df = df.dropna()

df.to_csv("data/processed/adhd_final.csv", index=False)

print("Final feature selection done")
print(df.head())