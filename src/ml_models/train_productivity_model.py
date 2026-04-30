import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error
from catboost import CatBoostRegressor
import joblib
import numpy as np

# Load dataset
df = pd.read_csv("data/featured/behavioral_scaled.csv")

X = df.drop("productivity_score", axis=1)

# Log transform the target variable to handle skewness and improve performance
y = np.log1p(df["productivity_score"])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Use CatBoost with Early Stopping and Regularization to prevent overfitting
model = CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    l2_leaf_reg=5, # Regularization to prevent overfitting
    verbose=100,
    random_state=42
)

# The eval_set and early_stopping_rounds stop the model before it memorizes the training data
model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=50)

best_model = model

# Cross validation on full data
cv_score = cross_val_score(best_model, X, y, cv=5, scoring="r2").mean()

# Convert back from log scale for meaningful metrics
y_train_orig = np.expm1(y_train)
pred_train_orig = np.expm1(best_model.predict(X_train))

y_test_orig = np.expm1(y_test)
pred_test_orig = np.expm1(best_model.predict(X_test))

# Metrics
print("\nCross Validation R2 (Log Scale):", cv_score)
print("Train R2 (Original Scale):", r2_score(y_train_orig, pred_train_orig))
print("Test R2 (Original Scale):", r2_score(y_test_orig, pred_test_orig))
print("MAE (Original Scale):", mean_absolute_error(y_test_orig, pred_test_orig))

# Save model
joblib.dump(best_model, "models/productivity_model.pkl")

print("\nFinal Productivity Model Saved!")