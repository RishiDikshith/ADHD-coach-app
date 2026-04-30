from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from chatbot.chatbot_engine import chatbot_response
from feature_engineering.feature_builder import build_features
from intervention.intervention_engine import generate_interventions
from scoring.adhd_questionnaire_score import calculate_adhd_score
from scoring.adhd_scoring import combined_adhd_score
from scoring.final_score import final_score
from scoring.mental_health_scoring import mental_health_score
from scoring.productivity_scoring import productivity_score
from scoring.student_scoring import depression_score
from utils.helpers import align_features_to_model, get_model_feature_names, prepare_model_for_inference

BASE_DIR = Path(__file__).resolve().parents[1]


def predict_mental_health_probability(model, text):
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([text])[0]
        classes = [str(value).lower() for value in getattr(model, "classes_", [])]

        if "1" in classes:
            return float(probabilities[classes.index("1")])
        if "stress" in classes:
            return float(probabilities[classes.index("stress")])
        return float(np.max(probabilities))

    label = str(model.predict([text])[0]).lower()
    return 1.0 if label in {"1", "stress"} else 0.0


def heuristic_depression_prediction(user_data):
    stress_level = user_data.get("stress_level", 5)
    sleep_hours = user_data.get("sleep_hours", 7)
    return int(stress_level >= 8 and sleep_hours < 6)


# Load models
productivity_model = prepare_model_for_inference(joblib.load(BASE_DIR / "models" / "productivity_model.pkl"))
adhd_model = prepare_model_for_inference(joblib.load(BASE_DIR / "models" / "adhd_risk_model.pkl"))
mental_health_model = prepare_model_for_inference(joblib.load(BASE_DIR / "models" / "mental_health_nlp_pipeline.pkl"))
student_model = prepare_model_for_inference(joblib.load(BASE_DIR / "models" / "student_model.pkl"))

# -------------------------
# SAMPLE INPUT
# -------------------------
user_data = {
    "age": 21,
    "gender": 1,
    "study_hours_per_day": 4,
    "sleep_hours": 5,
    "phone_usage_hours": 6,
    "social_media_hours": 2,
    "youtube_hours": 2,
    "gaming_hours": 1,
    "breaks_per_day": 3,
    "coffee_intake_mg": 100,
    "exercise_minutes": 20,
    "stress_level": 8
}

adhd_answers = ["Often", "Sometimes", "Rarely", "Often", "Very Often"]
text_input = "I feel stressed and distracted"

# -------------------------
# PIPELINE
# -------------------------
df = pd.DataFrame([user_data])
df = build_features(df)

prod_pred = productivity_model.predict(align_features_to_model(df, productivity_model))[0]
adhd_raw = adhd_model.predict(align_features_to_model(df, adhd_model))[0]

# Normalize safely to 0-1
adhd_risk = max(0, min(1, adhd_raw / 100))
mh_pred = predict_mental_health_probability(mental_health_model, text_input)

student_feature_names = get_model_feature_names(student_model) or []
if student_feature_names and all(name in df.columns for name in student_feature_names):
    dep_pred = student_model.predict(align_features_to_model(df, student_model))[0]
else:
    dep_pred = heuristic_depression_prediction(user_data)

# Scoring
prod_score = productivity_score(prod_pred)
q_score, q_level = calculate_adhd_score(adhd_answers)
adhd_health, final_adhd_risk = combined_adhd_score(q_score, adhd_risk)
mh_score = mental_health_score(mh_pred)
dep_score = depression_score(dep_pred)

final, level, description, weights = final_score(
    prod_score,
    adhd_health,
    mh_score,
    dep_score
)

# Recommendations
rec = generate_interventions(
    user_data,
    {
        "productivity": prod_score,
        "adhd_risk": final_adhd_risk,
        "mental_health": mh_score,
        "depression": dep_score
    }
)

# Chatbot
chat = chatbot_response(
    text_input,
    scores={
        "productivity": prod_score,
        "adhd_risk": final_adhd_risk,
        "mental_health": mh_score,
        "depression": dep_score
    },
    user_data=user_data
)

# -------------------------
# OUTPUT
# -------------------------
print("\n===== RESULTS =====")
print("Productivity:", prod_score)
print("ADHD Risk:", round(final_adhd_risk, 2))
print("ADHD Questionnaire Level:", q_level)
print("Mental Health:", mh_score)
print("Depression:", dep_score)

print("\nFinal Score:", round(final, 2))
print("Level:", level)
print("Description:", description)
print("Weights used:", {k: round(v, 3) for k, v in weights.items()})

print("\nRecommendations:")
for r in rec:
    print(f"- [{r['priority'].upper()}] {r['title']}: {r['action']}")

print("\nChatbot:", chat)
