import pandas as pd

df = pd.read_csv("data/raw/adhd_screening_data.csv", encoding="latin1")

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns)

print("\nMissing Values:")
print(df.isnull().sum().sort_values(ascending=False).head(20))

# Column groups
asrs_cols = [c for c in df.columns if "asrs" in c]
bdi_cols = [c for c in df.columns if "bdi" in c]
bai_cols = [c for c in df.columns if "bai" in c]
audit_cols = [c for c in df.columns if "audit" in c]
aas_cols = [c for c in df.columns if "aas" in c]
nbt_cols = [c for c in df.columns if "nbt" in c]

print("\nASRS Columns:", len(asrs_cols))
print("BDI Columns:", len(bdi_cols))
print("BAI Columns:", len(bai_cols))
print("AUDIT Columns:", len(audit_cols))
print("AAS Columns:", len(aas_cols))
print("NBT Columns:", len(nbt_cols))