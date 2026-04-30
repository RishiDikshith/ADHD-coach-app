import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

df = pd.read_csv("data/cleaned/mental_health_cleaned.csv")

print("Before cleaning NaN:", df.shape)

# Remove NaN text rows
df = df.dropna(subset=["cleaned_text"])

# Remove empty strings
df = df[df["cleaned_text"].str.strip() != ""]

print("After cleaning NaN:", df.shape)

vectorizer = TfidfVectorizer(max_features=1000)

X = vectorizer.fit_transform(df["cleaned_text"])

# Save vectorizer
pickle.dump(vectorizer, open("models/tfidf_vectorizer.pkl", "wb"))

# Convert to dataframe
X_df = pd.DataFrame(X.toarray())
X_df["label"] = df["label"].values

X_df.to_csv("data/featured/mental_health_vectorized.csv", index=False)

print("Vectorization completed")