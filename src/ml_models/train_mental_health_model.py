import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

data_path = "data/cleaned/mental_health_cleaned.csv"
print(f"Loading strictly local dataset from: {os.path.abspath(data_path)}")
df = pd.read_csv(data_path)

# Remove NaN and empty text
df = df.dropna(subset=["cleaned_text"])
df = df[df["cleaned_text"].str.strip() != ""]

print("Dataset after cleaning:", df.shape)

X = df["cleaned_text"].tolist()
y = df["label"].tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Create a simple, fast NLP pipeline using TF-IDF and Logistic Regression
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
    ("clf", LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000))
])

print("Training TF-IDF + Logistic Regression model...")
pipeline.fit(X_train, y_train)

# Evaluate
print("Evaluating model...")
preds = pipeline.predict(X_test)
print(classification_report(y_test, preds))
print("Accuracy:", accuracy_score(y_test, preds))

# Save the pipeline
joblib.dump(pipeline, "models/mental_health_nlp_pipeline.pkl")
print("\nMental Health TF-IDF model saved successfully to models/mental_health_nlp_pipeline.pkl!")
