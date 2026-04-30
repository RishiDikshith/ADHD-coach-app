import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

# 1. Load Data
# Assuming 'student_scaled.csv' is already pre-processed
df = pd.read_csv("data/featured/student_scaled.csv")
target = "Do you have Depression?"

X = df.drop(target, axis=1)
y = df[target]

# 2. Train-Test Split (Crucial BEFORE SMOTE)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. Apply SMOTE ONLY to the training data
# This ensures our test set remains 100% pure, unseen human data
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

# 4. Model Definition
# Use single-threaded training for compatibility with restricted environments.
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=1
)

# 4.5. Evaluate with Cross-Validation to get a reliable performance metric
pipeline = Pipeline([('smote', SMOTE(random_state=42)), ('model', model)])
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
print(f"--- Cross-Validation Accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f}) ---")

# 5. Final Training
model.fit(X_train_resampled, y_train_resampled)

# 6. Evaluation on Unseen Test Data
y_pred = model.predict(X_test)
print("--- Unseen Test Data Classification Report ---")
print(classification_report(y_test, y_pred))

# 7. Export the model
joblib.dump(model, "models/student_model.pkl")

print("Student model saved successfully in 'models/student_model.pkl'")
