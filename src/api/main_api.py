import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Add the 'src' directory to the Python path to resolve module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from feature_engineering.feature_builder import build_features
from intervention.intervention_engine import generate_interventions
from scoring.adhd_questionnaire_score import calculate_adhd_score
from scoring.adhd_scoring import combined_adhd_score
from scoring.final_score import final_score
from scoring.mental_health_scoring import mental_health_score
from scoring.productivity_scoring import productivity_score
from scoring.student_scoring import depression_score
from utils.helpers import align_features_to_model, get_model_feature_names, prepare_model_for_inference
from ml_models.efficient_inference import (
    EfficientInference, 
    load_model_cached,
    align_features_optimized,
    cached_predict,
    store_prediction
)

# Logging is now configured at the application entry point (frontend/app.py)
# to ensure it's set up correctly for the cloud environment.
app = FastAPI(title="ADHD Productivity API")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
STRESS_KEYWORDS = {
    "stress", "stressed", "overwhelm", "overwhelmed", "anxious", "panic",
    "too much", "hard", "stuck", "tired", "sad", "depressed", "burned out"
}


# -------- EFFICIENT MODEL LOADING WITH CACHING --------
try:
    adhd_inference = EfficientInference(
        str(MODELS_DIR / "adhd_risk_model.pkl"), 
        "ADHD Risk Model"
    )
    logging.info("✅ ADHD Risk Model loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load ADHD model: {e}")
    adhd_inference = None

try:
    productivity_inference = EfficientInference(
        str(MODELS_DIR / "productivity_model.pkl"), 
        "Productivity Model"
    )
    logging.info("✅ Productivity Model loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load Productivity model: {e}")
    productivity_inference = None

try:
    student_inference = EfficientInference(
        str(MODELS_DIR / "student_model.pkl"), 
        "Student Depression Model"
    )
    logging.info("✅ Student Depression Model loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load Student model: {e}")
    student_inference = None

try:
    mental_pipeline = load_model_cached(str(MODELS_DIR / "mental_health_nlp_pipeline.pkl"))
    mental_pipeline = prepare_model_for_inference(mental_pipeline)
    logging.info("✅ Mental Health NLP Pipeline loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load Mental Health model: {e}")
    mental_pipeline = None

# Fallback for backward compatibility
adhd_model = adhd_inference.model if adhd_inference else None
productivity_model = productivity_inference.model if productivity_inference else None
student_depression_model = student_inference.model if student_inference else None

SYSTEM_PROMPT = """
You are an empathetic ADHD productivity coach AI assistant. Your primary goal is to provide clear, actionable, and supportive guidance in a format that is easy for a user with ADHD to digest.

**RESPONSE FORMATTING RULES (MUST FOLLOW):**
1.  **Use Markdown:** Always use Markdown for formatting. Use `*` for bullet points and `**` for bolding key terms.
2.  **Structure with Lists:** Break down advice, suggestions, or questions into a bulleted or numbered list. Avoid long paragraphs.
3.  **Keep it Concise:** Sentences must be short. Each bullet point should contain only one main idea.
4.  **Empathetic Opener:** Start with one or two sentences of empathy and validation.
5.  **Action-Oriented:** Immediately follow the opener with actionable, small steps (micro-actions) or clarifying questions in a list format.

**Example of a good response:**
"It sounds like you're feeling really overwhelmed right now, and that's completely understandable. Let's try to break it down into tiny pieces.

Here are a couple of ideas:
*   Could you tell me what the *very first* small step of your task is?
*   Alternatively, we could try a 5-minute "body doubling" focus session right here.

Which one feels more manageable?"

**Core Mission:**
- Help users with ADHD-related challenges like focus, time management, motivation, and organization.
- Personalize responses based on the user's emotional state and productivity level.
- Always be encouraging and practical.
"""


class ChatRequest(BaseModel):
    text: str
    history: List[Any] = Field(default_factory=list)
    user_data: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)


class ScoreRequest(BaseModel):
    user_data: Dict[str, Any] = Field(default_factory=dict)
    adhd_answers: List[str] = Field(default_factory=list)
    text: str = ""


class InterventionRequest(BaseModel):
    user_data: Dict[str, Any] = Field(default_factory=dict)
    scores: Dict[str, Any] = Field(default_factory=dict)


def select_features(df: pd.DataFrame, model):
    if model is None:
        return df
    return align_features_to_model(df, model)


def predict_mental_health_probability(text: str):
    """
    Predict mental health probability combining ML model and stress text analysis.
    
    Uses both ML model (if available) and keyword-based stress detection
    to provide more realistic and reliable stress assessment.
    """
    if not text:
        return None

    # Try ML model first
    ml_probability = None
    if mental_pipeline is not None:
        try:
            if hasattr(mental_pipeline, "predict_proba"):
                probabilities = mental_pipeline.predict_proba([text])[0]
                classes = [str(value).lower() for value in getattr(mental_pipeline, "classes_", [])]

                if "1" in classes:
                    ml_probability = float(probabilities[classes.index("1")])
                elif "stress" in classes:
                    ml_probability = float(probabilities[classes.index("stress")])
                else:
                    ml_probability = float(np.max(probabilities))
            else:
                prediction = str(mental_pipeline.predict([text])[0]).lower()
                ml_probability = 1.0 if prediction in {"1", "stress"} else 0.0
        except Exception:
            logging.debug("ML mental health prediction failed, using text analysis")
            ml_probability = None

    # Use advanced stress text analysis
    from scoring.mental_health_scoring import analyze_stress_text
    stress_probability = analyze_stress_text(text)

    # Combine both approaches for better accuracy
    if ml_probability is not None:
        # Blend ML model with stress analysis (60% ML, 40% stress analysis)
        combined_probability = (ml_probability * 0.6) + (stress_probability * 0.4)
        return float(np.clip(combined_probability, 0.0, 1.0))
    else:
        # Fallback: use stress analysis only
        return float(stress_probability)


def student_model_has_usable_inputs(df: pd.DataFrame) -> bool:
    if student_inference is None:
        return False
    
    feature_count = student_inference.get_feature_count()
    return feature_count > 0 and len(df.columns) >= feature_count * 0.8


def estimate_depression_health_score(user_data: Dict[str, Any], engineered_df: pd.DataFrame) -> float:
    if student_inference is not None and student_model_has_usable_inputs(engineered_df):
        try:
            # Use optimized batch prediction
            predicted_label = student_inference.predict(engineered_df)[0]
            return float(depression_score(predicted_label))
        except Exception as e:
            logging.warning(f"Student model prediction failed: {e}")
    
    # Fallback to heuristic
    stress_level = user_data.get("stress_level", 5)
    sleep_hours = user_data.get("sleep_hours", 7)
    estimated_risk = min(1.0, max(0.0, (stress_level / 10) * 0.7 + max(0, 7 - sleep_hours) * 0.08))
    return float(max(20, min(85, (1 - estimated_risk) * 100)))


def build_user_scores(user_data: Dict[str, Any], text: str = "", adhd_answers: List[str] | None = None) -> Dict[str, Any]:
    if not user_data:
        return {}

    adhd_answers = adhd_answers or []
    user_snapshot = dict(user_data)

    calculated_stress = user_snapshot.get("stress_level", 5)
    user_snapshot["stress_level"] = calculated_stress

    engineered_df = build_features(pd.DataFrame([user_snapshot]))

    try:
        if productivity_inference is None:
            raise ValueError("Productivity model unavailable")
        # Use optimized inference with caching
        productivity_raw = np.expm1(productivity_inference.predict(engineered_df)[0])
        productivity_pct = float(productivity_score(productivity_raw))
    except Exception:
        logging.exception("Productivity scoring failed")
        productivity_pct = 50.0

    try:
        if adhd_inference is None:
            raise ValueError("ADHD model unavailable")
        # Use optimized inference with caching and batch processing
        adhd_raw = adhd_inference.predict(engineered_df)[0]
        adhd_risk = max(0.0, min(1.0, adhd_raw / 100 if adhd_raw > 1 else adhd_raw))
    except Exception:
        logging.exception("ADHD scoring failed")
        adhd_risk = 0.5

    if adhd_answers:
        questionnaire_score, questionnaire_level = calculate_adhd_score(adhd_answers)
        adhd_health_pct, final_adhd_risk = combined_adhd_score(questionnaire_score, adhd_risk)
    else:
        questionnaire_score, questionnaire_level = None, None
        final_adhd_risk = adhd_risk
        adhd_health_pct = max(0, min(100, (1 - adhd_risk) * 100))

    mental_health_probability = predict_mental_health_probability(text)
    if mental_health_probability is not None:
        mental_health_pct = float(mental_health_score(mental_health_probability))
    else:
        mental_health_pct = float(max(0, min(100, 100 - (calculated_stress * 10))))

    depression_pct = estimate_depression_health_score(user_snapshot, engineered_df)

    final, level, description, weights = final_score(
        productivity_pct,
        float(adhd_health_pct),
        mental_health_pct,
        depression_pct
    )

    if final_adhd_risk >= 0.7 or user_snapshot.get("stress_level", 0) >= 8:
        focus_risk = "high"
    elif final_adhd_risk < 0.3 and user_snapshot.get("stress_level", 0) <= 4:
        focus_risk = "low"
    else:
        focus_risk = "medium"

    return {
        "productivity_score": float(round(productivity_pct, 1)),
        "adhd_risk": float(round(final_adhd_risk, 2)),
        "adhd_health_score": float(round(adhd_health_pct, 1)),
        "adhd_questionnaire_score": questionnaire_score,
        "adhd_questionnaire_level": questionnaire_level,
        "mental_health_score": float(round(mental_health_pct, 1)),
        "depression_score": float(round(depression_pct, 1)),
        "final_score": float(round(final, 1)),
        "level": level,
        "description": description,
        "weights": {key: float(round(value, 3)) for key, value in weights.items()},
        "focus_risk": focus_risk,
        "summary": {
            "sleep_hours": user_snapshot.get("sleep_hours", 0),
            "stress_level": user_snapshot.get("stress_level", 0),
            "phone_distractions": user_snapshot.get("phone_distractions", 0),
            "study_hours": user_snapshot.get("study_hours_per_day", 0),
            "total_screen_time": float(
                engineered_df.get("total_screen_time", pd.Series([0])).iloc[0]
            )
        }
    }


def analyze(text):
    try:
        predicted_probability = predict_mental_health_probability(text)
        if predicted_probability is None:
            prompt_lower = text.lower()
            emotion_label = "stress" if any(keyword in prompt_lower for keyword in STRESS_KEYWORDS) else "normal"
        else:
            emotion_label = "stress" if predicted_probability >= 0.5 else "normal"

        productivity = "low" if len(text) < 30 else "medium"

        return {
            "emotion": emotion_label,
            "productivity": productivity
        }
    except Exception as exc:
        logging.error("Analysis error: %s", exc)
        return {
            "emotion": "normal",
            "productivity": "medium"
        }


def format_history(history):
    if not history:
        return "None"

    formatted = []
    for item in history[-5:]:
        if isinstance(item, dict):
            role = item.get("role", "user")
            content = item.get("content", "")
            formatted.append(f"{role}: {content}")
        else:
            formatted.append(str(item))

    return " ".join(formatted)


def build_prompt(user_input: str, analysis: Dict[str, Any], history: List[Any], scores: Dict[str, Any] = None):
    history_text = format_history(history)
    scores = scores or {}

    score_summary = ""
    if scores:
        score_summary = f"""
Score Summary:
- Productivity: {scores.get('productivity_score', 'N/A')}%
- ADHD Focus Risk: {scores.get('adhd_risk', 0)}
- Mental Health: {scores.get('mental_health_score', 'N/A')}%
- Sleep Quality: {scores.get('summary', {}).get('sleep_hours', 'N/A')} hours
- Stress Level: {scores.get('summary', {}).get('stress_level', 'N/A')}/10
- Focus Risk Level: {scores.get('focus_risk', 'unknown')}
- Overall Score: {scores.get('final_score', 'N/A')}
"""

    context = f"""
User's current emotional state: {analysis['emotion']}
User's productivity level: {analysis['productivity']}
Conversation history: {history_text}
{score_summary}
"""

    if not history:
        instruction = "Your goal is to understand the user's main challenge today. Ask an open-ended question to get them started."
    else:
        instruction = "The user is describing their problem. Ask clarifying questions to understand the root cause. Show empathy based on their emotional state."

    if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
        instruction += "\n\nCRITICAL INSTRUCTION: The user is experiencing HIGH STRESS. Be extremely gentle, empathetic, and validating. Do not push for heavy productivity right now. Focus on grounding, deep breaths, and emotional support."

    prompt = f"""
{SYSTEM_PROMPT}

{context}

---
Your instructions for this specific turn: {instruction}
---

User input: "{user_input}"

Respond naturally and helpfully to the user's input, following your instructions. Provide personalized advice based on their state.
Remember: For ADHD users, micro-actions (2-5 min tasks) work better than big plans.
"""

    return prompt


def generate_offline_reply(prompt):
    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["focus", "distract", "attention", "overwhelm", "concentration"]):
        return (
            "I can help with ADHD-friendly focus support. Try breaking your work into a tiny first step, "
            "set a short timer for 5-10 minutes, and remove one distraction from your space. "
            "Together we can build momentum from there."
        )
    if any(keyword in prompt_lower for keyword in ["time", "schedule", "plan", "deadline", "routine"]):
        return (
            "Time management is easier when you use small, visible blocks. "
            "Start with a single 10-minute task, set an alarm for the next step, "
            "and keep the next action simple."
        )
    if any(keyword in prompt_lower for keyword in ["motivation", "procrast", "lazy", "energy"]):
        return (
            "Motivation often comes after starting. Choose the smallest possible action, "
            "do it for just 2-5 minutes, and reward yourself for showing up."
        )
    return (
        "I'm here to help with ADHD-friendly strategies. "
        "Try a quick brain dump, then pick one tiny task and begin. "
        "If you want, I can simplify your current work right now."
    )


def get_ai_reply(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:instruct",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        res.raise_for_status()
        return res.json().get("response", "")
    except requests.exceptions.Timeout:
        logging.error("Ollama request timed out")
        return generate_offline_reply(prompt)
    except requests.exceptions.RequestException as exc:
        logging.error("Ollama request failed: %s", exc)
        return generate_offline_reply(prompt)
    except Exception:
        logging.exception("Unexpected error calling Ollama")
        return generate_offline_reply(prompt)


def format_reply(reply):
    return reply.strip()


@app.post("/chat")
def chat(data: ChatRequest):
    try:
        analysis = analyze(data.text)
        scores = build_user_scores(data.user_data, text=data.text) if data.user_data else {}
        prompt = build_prompt(data.text, analysis, data.history, scores)
        raw = get_ai_reply(prompt)
        reply = format_reply(raw)

        interventions = generate_interventions(data.user_data, scores) if data.user_data else []

        logging.info(
            "Chat completed: text=%s emotion=%s adhd_risk=%s",
            data.text,
            analysis.get("emotion"),
            scores.get("adhd_risk", "N/A")
        )
        return {
            "reply": reply,
            "analysis": analysis,
            "scores": scores,
            "interventions": interventions
        }
    except Exception:
        logging.exception("Error in /chat endpoint")
        return {
            "reply": "Backend processing error",
            "analysis": {"emotion": "normal", "productivity": "medium"},
            "scores": {},
            "interventions": []
        }


@app.post("/calculate_scores")
def calculate_scores(request: ScoreRequest):
    scores = build_user_scores(
        request.user_data,
        text=request.text,
        adhd_answers=request.adhd_answers
    )
    interventions = generate_interventions(request.user_data, scores)
    return {"scores": scores, "interventions": interventions}


@app.post("/get_interventions")
def get_interventions_endpoint(request: InterventionRequest):
    interventions = generate_interventions(request.user_data, request.scores)
    return {"interventions": interventions}
