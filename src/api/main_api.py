import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
from functools import lru_cache
import threading
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
from memory.memory_manager import MemoryManager
from agents.orchestrator import AgentOrchestrator
from task_paralysis.recovery_engine import TaskParalysisRecoveryEngine
from analytics.insight_engine import InsightEngine
from analytics.pattern_analyzer import PatternAnalyzer
from analytics.recommendation_engine import RecommendationEngine

# === NEW SYSTEM IMPORTS ===
from database.models import init_db, get_db
from database.crud import DatabaseManager
from auth.auth_handler import AuthHandler, get_password_hash, sanitize_input, sanitize_prompt, rate_limiter, sanitize_username, require_user, require_coach, require_admin, optional_user
from task_paralysis.state_detector import ADHDStateDetector
from intervention.adaptive_coach import AdaptiveCoach
from focus.focus_engine import FocusEngine
from gamification import GamificationEngine
from ai_engine.rag_engine import RAGEngine, LLMRouter

# Global analytics engine instances (lazy initialized per user)
_insight_engines = {}
_pattern_analyzers = {}
_recommendation_engines = {}
_db_manager = None
EAGER_TASK_RESULTS = {}

# Logging is now configured at the application entry point (frontend/app.py)
# to ensure it's set up correctly for the cloud environment.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and other resources on startup."""
    # Validate environment variables
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    is_prod = env in ("production", "prod", "staging")
    missing_vars = []
    for var in ["DATABASE_URL", "GROQ_API_KEY", "JWT_SECRET"]:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        msg = f"Critical environment variables missing at startup: {', '.join(missing_vars)}"
        if is_prod:
            logging.critical(f"FATAL: {msg}")
            raise RuntimeError(msg)
        else:
            logging.warning(f"WARNING: {msg} (Proceeding in development mode)")

    global _db_manager, _state_detector, _adaptive_coach, _focus_engine, _gamification, _rag_engine
    logging.info("Initializing database...")
    try:
        init_db()
        _db_manager = DatabaseManager()

        # Initialize dependent services AFTER db_manager is ready
        auth_handler.db = _db_manager
        _state_detector = ADHDStateDetector(_db_manager)
        _adaptive_coach = AdaptiveCoach(_db_manager, _state_detector)
        _focus_engine = FocusEngine(_db_manager)
        _gamification = GamificationEngine(_db_manager)
        _rag_engine = RAGEngine(None, _db_manager)

        logging.info("✅ Database and all services initialized successfully")
    except Exception as e:
        logging.warning(f"Database initialization skipped: {e}")
        _db_manager = None
        _state_detector = ADHDStateDetector(None)
        _adaptive_coach = AdaptiveCoach(None, _state_detector)
        _focus_engine = FocusEngine(None)
        _gamification = GamificationEngine(None)
        _rag_engine = RAGEngine(None, None)
    yield
    # Cleanup
    if _db_manager:
        _db_manager.close()

app = FastAPI(title="ADHD Productivity API", lifespan=lifespan)

# CORS middleware — required for frontend (localhost:3000) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001",
        "http://127.0.0.1:3000", os.getenv("FRONTEND_URL", ""),
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz(db = Depends(get_db)):
    from sqlalchemy import text
    try:
        # Test DB connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Register real-time WebSocket routes for co-working, accountability, and low-latency chat
from realtime.websocket_handlers import router as websocket_router
app.include_router(websocket_router)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
STRESS_KEYWORDS = {
    "stress", "stressed", "overwhelm", "overwhelmed", "anxious", "panic",
    "too much", "hard", "stuck", "tired", "sad", "depressed", "burned out",
    "tension", "tense", "cant focus", "can't focus", "cant understand", "can't understand"
}
POSITIVE_KEYWORDS = {
    "happy", "great", "good", "awesome", "fantastic", "amazing", "productive",
    "done", "finished", "excited", "glad", "joy", "better", "calm", "relaxed"
}
PRODUCTIVE_KEYWORDS = {
    "productive", "done", "finished", "completed", "focused", "progress",
    "did it", "working", "achieved", "accomplished", "on track", "next"
}
UNPRODUCTIVE_KEYWORDS = {
    "distracted", "procrastinating", "lazy", "unproductive", "cant focus",
    "can't focus", "behind", "stuck", "failing", "off track", "cant understand", "can't understand"
}

# -------- AUTH HANDLER (lazily initialized in lifespan) --------
auth_handler = AuthHandler(None)

# -------- GLOBAL INSTANCES (lazily initialized in lifespan) --------
_state_detector = None
_adaptive_coach = None
_focus_engine = None
_gamification = None
_rag_engine = None
_llm_router = LLMRouter()

# -------- EFFICIENT MODEL LOADING WITH CACHING --------
try:
    adhd_inference = EfficientInference(str(MODELS_DIR / "adhd_risk_model.pkl"), "ADHD Risk Model")
    logging.info("✅ ADHD Risk Model loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load ADHD model: {e}")
    adhd_inference = None

try:
    productivity_inference = EfficientInference(str(MODELS_DIR / "productivity_model.pkl"), "Productivity Model")
    logging.info("✅ Productivity Model loaded with optimization")
except Exception as e:
    logging.error(f"Failed to load Productivity model: {e}")
    productivity_inference = None

try:
    student_inference = EfficientInference(str(MODELS_DIR / "student_model.pkl"), "Student Depression Model")
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

adhd_model = adhd_inference.model if adhd_inference else None
productivity_model = productivity_inference.model if productivity_inference else None
student_depression_model = student_inference.model if student_inference else None

SYSTEM_PROMPT = """You are an empathetic, dynamic, and deeply personalized ADHD executive function coach. You are NOT a generic productivity bot — you are a specialized assistant who deeply understands how the ADHD brain works.

**YOUR ADHD EXPERTISE:**
- You know ADHD is not a lack of willpower — it's a difference in brain chemistry and executive function
- You understand task paralysis, time blindness, rejection sensitivity, hyperfocus, and emotional dysregulation
- You know that shame is the enemy of progress for ADHD brains
- You adapt your approach based on the user's current energy, stress, and focus patterns
- You celebrate micro-wins because consistent small steps > occasional big efforts
- You NEVER use shame, guilt, or toxic productivity language

**ADAPTIVE COACHING STYLE:**
1. **MATCH THE USER'S STATE:**
   - If stressed/overwhelmed: Be extra gentle, prioritize emotional support over productivity
   - If energetic/positive: Be encouraging, help channel the energy productively
   - If neutral: Be warm and help them find their focus
   - If in hyperfocus: Gently remind about basic needs (water, food, breaks)

2. **ADHD-FRIENDLY COMMUNICATION:**
   - Use VERY short paragraphs (2-3 sentences max per paragraph)
   - Use emojis strategically for emotional tone and dopamine
   - Use bold sparingly for emphasis on key points
   - End EVERY response with ONE specific, gentle question
   - Validate feelings BEFORE giving advice

3. **TASK STRATEGIES:**
   - Always suggest the SMALLEST possible version of a task
   - Use the "2-minute rule": anything worth doing is worth doing for 2 minutes
   - Frame tasks as suggestions, not commands
   - Include at least one body-based suggestion (water, movement, breathing)

4. **EMOTIONAL INTELLIGENCE:**
   - Validate: "It makes sense that you feel this way"
   - Normalize: "This is really common for ADHD brains"
   - Empower: "You've gotten through hard things before"
   - Never dismiss: Don't say "just do it" or "it's easy"

**FORMAT:**
REPLY:
[Your conversational response. Warm, validating, adaptive to user state. Use short paragraphs. End with ONE question.]

TASKS:
[1-3 tiny, actionable micro-steps. Each should take 2-5 minutes max. Use emojis.]

**CRITICAL: If the [ADHD AGENT INSIGHTS] section above flags HIGH STRESS, BURNOUT, or TASK PARALYSIS — prioritize emotional support and grounding over productivity. Suggest recovery, not more work.**
"""

# ==================== Request Models ====================

class ChatRequest(BaseModel):
    text: str
    history: List[Any] = Field(default_factory=list)
    user_data: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    language_name: str = "English"
    username: str = "default"
    agent_id: Optional[str] = "productivity-coach"


class ScoreRequest(BaseModel):
    user_data: Dict[str, Any] = Field(default_factory=dict)
    adhd_answers: List[str] = Field(default_factory=list)
    text: str = ""

class InterventionRequest(BaseModel):
    user_data: Dict[str, Any] = Field(default_factory=dict)
    scores: Dict[str, Any] = Field(default_factory=dict)

from pydantic import field_validator
import re

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class PinLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v

class SetPinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("PIN must be exactly 4 digits")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username can only contain alphanumeric characters, underscores, hyphens, and dots")
        return v

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str = Field("", max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username can only contain alphanumeric characters, underscores, hyphens, and dots")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        if v and not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v

class ResetPasswordRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class SettingsUpdateRequest(BaseModel):
    theme: str = "dark"
    language: str = "en"
    notifications_enabled: bool = True
    notification_frequency: str = "medium"
    timer_duration: int = 25
    auto_check_in: bool = True
    sound_enabled: bool = True
    use_12h_format: bool = False
    coach_tone: str = "encouraging"
    focus_area: str = "general"
    overwhelm_mode_enabled: bool = False
    start_tiny_default: bool = False
    time_blindness_enabled: bool = True
    celebration_effects: bool = True
    voice_autospeak: bool = False
    voice_speed: float = 1.0
    voice_pitch: float = 1.0
    voice_accent: str = "auto"

class AgentAnalyzeRequest(BaseModel):
    agent_type: str
    context: Dict[str, Any] = Field(default_factory=dict)

class TaskParalysisRequest(BaseModel):
    task: str
    user_data: Dict[str, Any] = Field(default_factory=dict)

class FocusRecommendRequest(BaseModel):
    mode_id: str = "standard"
    focus_score: float = 0.5
    sessions_completed_today: int = 0
    stress_level: int = 5
    energy_level: int = 5
    fatigue: int = 5
    username: str = "default"


# ==================== Helper Functions ====================

def select_features(df: pd.DataFrame, model):
    if model is None:
        return df
    return align_features_to_model(df, model)

def predict_mental_health_probability(text: str):
    if not text:
        return None
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
    from scoring.mental_health_scoring import analyze_stress_text
    stress_probability = analyze_stress_text(text)
    if ml_probability is not None:
        combined_probability = (ml_probability * 0.6) + (stress_probability * 0.4)
        return float(np.clip(combined_probability, 0.0, 1.0))
    else:
        return float(stress_probability)

def student_model_has_usable_inputs(df: pd.DataFrame) -> bool:
    if student_inference is None:
        return False
    feature_count = student_inference.get_feature_count()
    return feature_count > 0 and len(df.columns) >= feature_count * 0.8

def estimate_depression_health_score(user_data: Dict[str, Any], engineered_df: pd.DataFrame) -> float:
    if student_inference is not None and student_model_has_usable_inputs(engineered_df):
        try:
            predicted_label = student_inference.predict(engineered_df)[0]
            return float(depression_score(predicted_label))
        except Exception as e:
            logging.warning(f"Student model prediction failed: {e}")
    stress_level = user_data.get("stress_level", 5)
    sleep_hours = user_data.get("sleep_hours", 7)
    estimated_risk = min(1.0, max(0.0, (stress_level / 10) * 0.7 + max(0, 7 - sleep_hours) * 0.08))
    return float(max(20, min(85, (1 - estimated_risk) * 100)))

def build_user_scores(user_data: Dict[str, Any], text: str = "", adhd_answers: List[str] | None = None, analysis: Dict[str, str] = None) -> Dict[str, Any]:
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
        productivity_raw = np.expm1(productivity_inference.predict(engineered_df)[0])
        productivity_pct = float(productivity_score(productivity_raw))
    except Exception:
        logging.exception("Productivity scoring failed")
        productivity_pct = 50.0
    try:
        if adhd_inference is None:
            raise ValueError("ADHD model unavailable")
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
    depression_pct = estimate_depression_health_score(user_snapshot, engineered_df)
    mental_health_probability = predict_mental_health_probability(text)
    if mental_health_probability is not None:
        mental_health_pct = float(mental_health_score(mental_health_probability))
        final_adhd_risk = min(1.0, final_adhd_risk + (mental_health_probability * 0.3))
        productivity_pct = max(0.0, productivity_pct - (mental_health_probability * 40.0))
        depression_pct = (depression_pct * 0.6) + (mental_health_pct * 0.4)
    else:
        mental_health_pct = float(max(0, min(100, 100 - (calculated_stress * 10))))
    if analysis:
        emotion = analysis.get("emotion", "neutral")
        prod = analysis.get("productivity", "medium")
        if emotion == "stress":
            final_adhd_risk = min(1.0, final_adhd_risk + 0.35)
            depression_pct = max(0.0, depression_pct - 30.0)
            mental_health_pct = max(0.0, mental_health_pct - 40.0)
        elif emotion == "positive":
            final_adhd_risk = max(0.0, final_adhd_risk - 0.25)
            depression_pct = min(100.0, depression_pct + 25.0)
            mental_health_pct = min(100.0, mental_health_pct + 30.0)
        if prod == "high":
            productivity_pct = min(100.0, productivity_pct + 35.0)
            final_adhd_risk = max(0.0, final_adhd_risk - 0.15)
        elif prod == "low":
            productivity_pct = max(0.0, productivity_pct - 35.0)
            final_adhd_risk = min(1.0, final_adhd_risk + 0.2)
    final, level, description, weights = final_score(
        productivity_pct, float(adhd_health_pct), mental_health_pct, depression_pct
    )
    focus_risk = "high" if final_adhd_risk >= 0.7 or user_snapshot.get("stress_level", 0) >= 8 else "low" if final_adhd_risk < 0.3 and user_snapshot.get("stress_level", 0) <= 4 else "medium"
    return {
        "productivity_score": float(round(productivity_pct, 1)),
        "adhd_risk": float(round(final_adhd_risk, 2)),
        "adhd_health_score": float(round(adhd_health_pct, 1)),
        "adhd_questionnaire_score": questionnaire_score,
        "adhd_questionnaire_level": questionnaire_level,
        "mental_health_score": float(round(mental_health_pct, 1)),
        "depression_score": float(round(depression_pct, 1)),
        "final_score": float(round(final, 1)),
        "level": level, "description": description,
        "weights": {key: float(round(value, 3)) for key, value in weights.items()},
        "focus_risk": focus_risk,
        "summary": {
            "sleep_hours": user_snapshot.get("sleep_hours", 0),
            "stress_level": user_snapshot.get("stress_level", 0),
            "phone_distractions": user_snapshot.get("phone_distractions", 0),
            "study_hours": user_snapshot.get("study_hours_per_day", 0),
            "total_screen_time": float(engineered_df.get("total_screen_time", pd.Series([0])).iloc[0])
        }
    }

def analyze(text):
    import json, re
    try:
        prompt = f"""Analyze the following text from a user seeking productivity and mental health coaching. Classify the user's emotion as exactly one of: 'positive', 'neutral', or 'stress'. Classify their productivity status as exactly one of: 'high', 'medium', or 'low'. Respond with ONLY a valid JSON object in this format: {{"emotion": "...", "productivity": "..."}}. Do not include any other text. Text to analyze: '{text}'"""
        raw_response = get_ai_reply(prompt)
        match = re.search(r'\{.*\}', raw_response.replace('\n', ' '), re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {"emotion": result.get("emotion", "neutral").lower(), "productivity": result.get("productivity", "medium").lower()}
    except Exception as e:
        logging.debug(f"LLM analysis failed, falling back to heuristics: {e}")
    try:
        predicted_probability = predict_mental_health_probability(text)
        prompt_lower = text.lower()
        if any(keyword in prompt_lower for keyword in POSITIVE_KEYWORDS):
            emotion_label = "positive"
        elif predicted_probability is None:
            emotion_label = "stress" if any(keyword in prompt_lower for keyword in STRESS_KEYWORDS) else "neutral"
        else:
            emotion_label = "stress" if predicted_probability >= 0.25 or any(keyword in prompt_lower for keyword in STRESS_KEYWORDS) else "neutral"
        if any(keyword in prompt_lower for keyword in PRODUCTIVE_KEYWORDS):
            productivity = "high"
        elif any(keyword in prompt_lower for keyword in UNPRODUCTIVE_KEYWORDS):
            productivity = "low"
        else:
            productivity = "medium"
        return {"emotion": emotion_label, "productivity": productivity}
    except Exception as exc:
        logging.error("Analysis error: %s", exc)
        return {"emotion": "normal", "productivity": "medium"}

def format_history(history):
    if not history:
        return "None"
    formatted = []
    for item in history[-5:]:
        if isinstance(item, dict):
            formatted.append(f"{item.get('role', 'user')}: {item.get('content', '')}")
        else:
            formatted.append(str(item))
    return " ".join(formatted)

def build_prompt(user_input, english_translation, analysis, history, scores=None, language="en", language_name="English", memory_context=""):
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
User's selected language: {language_name} ({language})
{score_summary}
{memory_context}
"""
    instruction = "Start by warmly welcoming the user and responding directly to their input." if not history else "Respond to the user as a supportive, dynamic friend."
    if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
        instruction += "\nCRITICAL: The user has HIGH STRESS. Be extremely gentle, warm, and deeply empathetic."
    prompt = f"""
{SYSTEM_PROMPT}

{context}

---
Your instructions for this specific turn: {instruction}
---

User input (Original): "{user_input}"
User input (English Translation context): "{english_translation}"

CRITICAL LANGUAGE RULE: You MUST reply in the EXACT SAME language and script as "User input (Original)".
CRITICAL FORMATTING: Avoid long paragraphs at all costs. Format your advice using short bullet points and a mix of emojis. End with a single question.

You MUST format your entire response exactly like this:

REPLY:
[Your conversational, multi-paragraph response here.]

TASKS:
[1 to 3 tiny, actionable tasks. List them with a dash e.g. "- Drink water"]
"""
    return prompt

def translate_to_english(text: str) -> str:
    if not text or len(text.strip()) < 2:
        return text
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated if translated else text
    except Exception as e:
        logging.debug(f"Translation to English failed: {e}")
        return text

def translate_reply_if_needed(reply: str, language: str):
    target_language = (language or "en").split("-")[0]
    if target_language == "en":
        return reply
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target=target_language).translate(reply)
    except Exception:
        return reply

def generate_offline_reply(prompt):
    prompt_lower = prompt.lower()
    if any(kw in prompt_lower for kw in ["focus", "distract", "attention", "overwhelm", "concentration"]):
        reply = """REPLY:
Hey there! It sounds like you're feeling pretty overwhelmed right now, which makes focusing incredibly difficult. That's completely normal and okay! 🌬️

Sometimes our brains just need a tiny reset before diving back in. Let's take it slow and try not to force it.

If we could pick just *one* super tiny thing to knock out right now, what would it be? 🤔

TASKS:
- Take 3 deep breaths
- Open your notes
- Start a 5-minute timer"""
    elif any(kw in prompt_lower for kw in ["time", "schedule", "plan", "deadline", "routine"]):
        reply = """REPLY:
Planning can definitely be tricky, especially when there's so much on your plate! 🗓️

Instead of looking at the whole schedule and getting stressed, let's just zoom in on right now.

What is the very next thing you need to do in the next 10 minutes to feel a little better? ⏳

TASKS:
- List top 3 priorities
- Pick the easiest one
- Block out 15 minutes"""
    elif any(kw in prompt_lower for kw in ["motivation", "procrast", "lazy", "energy"]):
        reply = """REPLY:
It's totally normal to hit a wall with motivation. We all have those days where our energy is just completely zapped! 🔋

Sometimes starting is the hardest part. What if we just do a 2-minute 'starter' task to build a tiny bit of momentum?

What's the absolute smallest possible step you could take right now? ✨

TASKS:
- Drink a glass of water
- Clear your desk space
- Do a 2-minute starter task"""
    else:
        reply = """REPLY:
I hear you, and I completely understand where you're coming from. I'm right here to support you! 🤝

Let's figure this out together step by step so it doesn't feel like too much.

What is the main thing you want us to tackle together today? 🚀

TASKS:
- Define your main goal for today
- Break it into 3 small steps
- Start the first step"""
    return reply

MAX_CONCURRENT_AI_REQUESTS = int(os.getenv("MAX_CONCURRENT_AI_REQUESTS", "4"))
ai_queue_semaphore = threading.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

@lru_cache(maxsize=1000)
def get_ai_reply(prompt, language: str = "en"):
    acquired = ai_queue_semaphore.acquire(timeout=15.0)
    if not acquired:
        return generate_offline_reply(prompt)
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            logging.warning("GROQ_API_KEY not set, falling back to offline reply")
            return generate_offline_reply(prompt)
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", temperature=0.7, max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as exc:
        logging.error("Groq API request failed: %s", exc)
        return generate_offline_reply(prompt)
    finally:
        ai_queue_semaphore.release()

def format_reply(reply):
    return reply.strip()

# ==================== Validation Error Handler for Auth ====================
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/auth/"):
        errors = exc.errors()
        err_msg = "Validation error"
        if errors:
            loc = errors[0].get("loc", [])
            field = loc[-1] if loc else "field"
            msg = errors[0].get("msg", "invalid value")
            err_msg = f"Invalid {field}: {msg}"
        return JSONResponse(
            status_code=200,
            content={"success": False, "error": err_msg}
        )
    # Default behavior for other endpoints
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)

# ==================== Rate Limiting Middleware ====================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    
    # 1. Classify endpoint category and set limits
    if path in ("/auth/login", "/auth/login-pin", "/auth/register"):
        max_req = 5
        window = 60
        category = "auth"
    elif path in ("/chat", "/calculate_scores", "/get_interventions"):
        max_req = 10
        window = 60
        category = "expensive"
    else:
        max_req = 100
        window = 60
        category = "general"
        
    # Create a unique key combining client IP and the category
    rate_key = f"{client_ip}:{category}"
    
    allowed, remaining = rate_limiter.check(rate_key, max_requests=max_req, window_seconds=window)
    if not allowed:
        # Structured log of rate limit blocking
        from src.utils.audit_logger import audit_log
        audit_log(
            username="anonymous",
            action="rate_limit_blocked",
            status="BLOCKED",
            ip_address=client_ip,
            details={"path": path, "category": category},
            severity="WARN"
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": str(window)}
        )
        
    # Call the next handler
    response = await call_next(request)
    
    # Inject RateLimit headers into response for transparency
    response.headers["X-RateLimit-Limit"] = str(max_req)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# ==================== AUTH ENDPOINTS (JWT + bcrypt) ====================

@app.post("/auth/register")
def auth_register(request: RegisterRequest, response: Response):
    sanitized_username = sanitize_username(request.username)
    if not sanitized_username:
        return {"success": False, "error": "Invalid username. Use 3-50 alphanumeric characters."}
    if len(request.password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}
    
    result = auth_handler.register_user(sanitized_username, request.password, request.email)
    if not result.get("success"):
        return result
        
    # Initialize DB user
    if _db_manager:
        _db_manager.get_or_create_user(sanitized_username, get_password_hash(request.password), request.email)
        
    # Delivery tokens via Secure, HttpOnly, SameSite strict cookies
    access_token = result.get("token")
    refresh_token = result.get("refresh_token")
    
    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=30 * 60,
        )
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 3600,
        )
        
    return result

@app.post("/auth/login")
def auth_login(request: AuthRequest, response: Response):
    sanitized_username = sanitize_username(request.username)
    if not sanitized_username:
        return {"success": False, "error": "Invalid username format"}
        
    if _db_manager:
        result = auth_handler.login_user(sanitized_username, request.password)
        if result.get("success"):
            _db_manager.update_streak(sanitized_username, "daily")
            
            # Delivery tokens via Secure, HttpOnly, SameSite strict cookies
            access_token = result.get("token")
            refresh_token = result.get("refresh_token")
            
            if access_token:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=30 * 60,
                )
            if refresh_token:
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=7 * 24 * 3600,
                )
        return result
    return {"success": False, "error": "Database not initialized"}

@app.post("/auth/refresh")
async def auth_refresh(request: Request, response: Response, payload: Optional[dict] = None):
    # Resolve token from request body or cookies
    refresh_token = None
    if payload:
        refresh_token = payload.get("refresh_token")
    if not refresh_token:
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except Exception:
            pass
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")
        
    if not refresh_token:
        return {"success": False, "error": "Refresh token required"}
        
    result = auth_handler.refresh_token(refresh_token)
    if result.get("success"):
        new_access = result.get("token")
        new_refresh = result.get("refresh_token")
        
        # Set updated secure cookies
        if new_access:
            response.set_cookie(
                key="access_token",
                value=new_access,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=30 * 60,
            )
        if new_refresh:
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=7 * 24 * 3600,
            )
    return result

@app.post("/auth/logout")
def auth_logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"success": True, "message": "Successfully logged out"}

@app.post("/auth/reset-password")
def auth_reset_password(request: ResetPasswordRequest):
    sanitized_username = sanitize_username(request.username)
    if not sanitized_username:
        return {"success": False, "error": "Invalid username"}
    if len(request.new_password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}
    if not _db_manager:
        return {"success": False, "error": "Database not available"}
    user = _db_manager.get_user(sanitized_username)
    if not user:
        return {"success": False, "error": "User not found"}
    if user.email != request.email:
        return {"success": False, "error": "Email does not match our records"}
    from auth.auth_handler import get_password_hash
    user.password_hash = get_password_hash(request.new_password)
    db = _db_manager.db
    db.commit()
    return {"success": True, "message": "Password reset successfully"}

@app.post("/auth/login-pin")
def auth_login_pin(request: PinLoginRequest, response: Response):
    sanitized_username = sanitize_username(request.username)
    if not sanitized_username:
        return {"success": False, "error": "Invalid username format"}

    if _db_manager:
        result = auth_handler.login_with_pin(sanitized_username, request.pin)
        if result.get("success"):
            _db_manager.update_streak(sanitized_username, "daily")

            # Delivery tokens via Secure, HttpOnly, SameSite strict cookies
            access_token = result.get("token")
            refresh_token = result.get("refresh_token")

            if access_token:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=30 * 60,
                )
            if refresh_token:
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    max_age=7 * 24 * 3600,
                )
        return result
    return {"success": False, "error": "Database not initialized"}

@app.get("/auth/has-pin/{username}")
def auth_has_pin(username: str):
    sanitized_username = sanitize_username(username)
    if not sanitized_username:
        return {"has_pin": False}
    if _db_manager:
        user = _db_manager.get_user(sanitized_username)
        if user and user.security_pin_hash:
            return {"has_pin": True}
    return {"has_pin": False}

@app.post("/auth/set-pin")
def auth_set_pin(request: SetPinRequest, current_user: str = Depends(require_user)):
    if _db_manager:
        user = _db_manager.get_user(current_user)
        if user:
            from auth.auth_handler import get_password_hash
            user.security_pin_hash = get_password_hash(request.pin)
            _db_manager.db.commit()
            return {"success": True, "message": "Security PIN set successfully"}
    return {"success": False, "error": "Database not available"}

@app.post("/auth/remove-pin")
def auth_remove_pin(current_user: str = Depends(require_user)):
    if _db_manager:
        user = _db_manager.get_user(current_user)
        if user:
            user.security_pin_hash = None
            _db_manager.db.commit()
            return {"success": True, "message": "Security PIN removed successfully"}
    return {"success": False, "error": "Database not available"}

@app.get("/settings/{username}")
def get_settings(username: str, active_user: Optional[str] = Depends(optional_user)):
    # Security: If a token is provided, verify ownership or admin access
    if active_user and active_user != username:
        if _db_manager:
            curr_db_user = _db_manager.get_user(active_user)
            if not curr_db_user or getattr(curr_db_user, "role", "user") != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if not _db_manager:
        return {"theme": "dark", "language": "en", "notifications_enabled": True}
    user = _db_manager.get_user(username)
    if not user:
        return {"theme": "dark", "language": "en", "notifications_enabled": True}
    return user.settings

@app.put("/settings/{username}")
def update_settings(username: str, settings: SettingsUpdateRequest, current_user: str = Depends(require_user)):
    # Security: Ensure user can only update their own settings, or is an admin!
    if current_user != username:
        if _db_manager:
            curr_db_user = _db_manager.get_user(current_user)
            if not curr_db_user or getattr(curr_db_user, "role", "user") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied. You can only update your own settings."
                )

    if not _db_manager:
        return {"success": False, "error": "Database not available"}
    updated = _db_manager.update_user_settings(username, settings.model_dump())
    if not updated:
        return {"success": False, "error": "User not found"}
        
    # Transaction Audit Log
    from src.utils.audit_logger import audit_log
    audit_log(
        username=username,
        action="update_settings",
        status="SUCCESS",
        details={"updated_fields": list(settings.model_dump().keys())}
    )
    
    return {"success": True, "settings": updated.settings}


# ==================== CHAT ENDPOINT (with RAG + Fact Extraction) ====================

@app.post("/chat")
def chat(data: ChatRequest):
    try:
        # === LANGUAGE AUTO-DETECTION ===
        if data.text and len(data.text.strip()) > 1:
            try:
                import langdetect
                detected = langdetect.detect(data.text)
                if detected and len(detected) == 2:
                    data.language = detected
            except Exception as e:
                logging.debug(f"Langdetect failed in /chat: {e}")

        username = data.username or "default"
        data.text = sanitize_prompt(data.text, username)
        memory = MemoryManager(user_id=username)
        orchestrator = AgentOrchestrator(memory)
        paralysis_engine = TaskParalysisRecoveryEngine(memory)

        # Connect memory to DB for fact extraction
        if _db_manager:
            memory.set_db_manager(_db_manager)
            _rag_engine.memory = memory

        # === ROUTE TO AGENT PERSONALITY ===
        agent_id = data.agent_id or "productivity-coach"
        current_streak = data.session_data.get('current_streak', 0) if data.session_data else 0

        # === RAG: Retrieve rich context from all memory sources ===
        rag_context = _rag_engine.retrieve_context(
            username=username,
            query=data.text,
            user_data=data.user_data,
            session_data=data.session_data,
        )

        # === LLM Router: Classify intent ===
        intent = _llm_router.classify_intent(data.text)
        route_instruction = _llm_router.format_response_instruction(intent)

        # Get agent context (passing agent_id)
        agent_context = orchestrator.get_context_for_prompt(data.text, current_streak, agent_id)
        agent_insights = agent_context.get("agent_insights", "")

        # === ADHD State Detection ===
        state_result = _state_detector.analyze(data.text, {
            "current_stress": data.user_data.get("stress_level", 5),
            "current_energy": data.user_data.get("energy_level", 5),
            "text": data.text,
        })
        state_prompt_ext = _state_detector.get_system_prompt_extension(data.text)

        # === Adaptive Coaching ===
        coach_extension = _adaptive_coach.get_system_prompt_extension(
            data.text,
            {"current_stress": data.user_data.get("stress_level", 5)},
            data.user_data.get("mood"),
        )

        # === Task Paralysis ===
        paralysis_result = paralysis_engine.process_user_message(data.text, agent_context)
        paralysis_prompt_ext = ""
        if paralysis_result["paralysis_detected"]:
            ext = paralysis_engine.get_system_prompt_extension(data.text, agent_context)
            if ext:
                paralysis_prompt_ext = ext
            memory.set_task_paralysis(True)

        # Mute ADHD/coaching insights for support-agent
        if agent_id == "support-agent":
            state_prompt_ext = ""
            coach_extension = ""
            paralysis_prompt_ext = ""

        # === Combine all context ===
        all_context_parts = [rag_context, agent_insights, state_prompt_ext, coach_extension, paralysis_prompt_ext, route_instruction]
        all_context = "\n\n".join([p for p in all_context_parts if p])

        english_text = translate_to_english(data.text)
        analysis_result = analyze(english_text)
        scores = build_user_scores(data.user_data, text=english_text, analysis=analysis_result) if data.user_data else {}

        # === ROUTE PROMPT TO SPECIFIC CHATBOT PERSONALITY ===
        agent_system_prompt = orchestrator.build_agent_specific_prompt(
            agent_id, data.text, agent_context, current_streak
        )

        # Inject standard instructions
        instruction = "Start by warmly welcoming the user and responding directly to their input." if not data.history else f"Respond to the user as the supportive {agent_id} companion."
        if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
            instruction += "\nCRITICAL: The user has HIGH STRESS. Be extremely gentle, warm, and deeply empathetic."

        prompt = f"""
{agent_system_prompt}

{all_context}

---
Your instructions for this specific turn: {instruction}
User's current emotional state: {analysis_result['emotion']}
User's productivity level: {analysis_result['productivity']}
---

User input (Original): "{data.text}"
User input (English Translation context): "{english_text}"

CRITICAL LANGUAGE RULE: You MUST reply in the EXACT SAME language and script as "User input (Original)".
CRITICAL FORMATTING: Keep your paragraphs extremely brief (2-3 sentences max). Use formatting like bold, lists, and emojis strategically. 

You MUST format your entire response exactly like this:

REPLY:
[Your conversational, multi-paragraph response here.]

TASKS:
[1 to 3 tiny, actionable tasks. List them with a dash e.g. "- Drink water"]
"""

        raw = get_ai_reply(prompt, data.language)

        reply_part = raw
        dynamic_tasks = []
        import re
        if re.search(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE):
            parts = re.split(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE)
            reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', parts[0], flags=re.IGNORECASE).strip()
            tasks_part = parts[1].strip()
            for line in tasks_part.split('\n'):
                line = line.strip()
                if line.startswith("-") or line.startswith("*") or line.startswith("☐"):
                    clean_task = re.sub(r'^[\-\*☐]\s*', '', line).strip()
                    if clean_task:
                        dynamic_tasks.append(clean_task)
                else:
                    clean_line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                    if clean_line and len(clean_line) > 2:
                        dynamic_tasks.append(clean_line)
            reply_part = f"{reply_part}\n\n**Tasks:**\n{tasks_part}"
        else:
            reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', raw, flags=re.IGNORECASE).strip()

        reply = format_reply(translate_reply_if_needed(reply_part, data.language))

        # Detect cross-agent handoffs
        handoff_suggestion = orchestrator.detect_handoff_suggestion(data.text, agent_id)

        # Record conversation, emotion, and extract facts
        memory.record_conversation_turn(
            user_message=data.text,
            assistant_message=reply[:500],
            interaction_type="chat",
            metadata={"language": data.language, "agent_id": agent_id}
        )
        memory.record_emotion(
            emotion=analysis_result.get("emotion", "neutral"),
            stress=scores.get("summary", {}).get("stress_level", 5),
        )

        # Persist chat to database
        if _db_manager:
            try:
                _db_manager.save_chat_message(username, "user", data.text, analysis_result.get("emotion"))
                _db_manager.save_chat_message(username, "assistant", reply[:1000])
            except Exception as e:
                logging.warning(f"Chat persistence error: {e}")

        # Award XP for chat interaction
        if _db_manager:
            try:
                _gamification.award_xp(username, "mood_checkin")
            except Exception:
                pass

        interventions = []
        if dynamic_tasks:
            for task in dynamic_tasks[:3]:
                emoji = "✓"
                if "breath" in task.lower(): emoji = "🧘"
                elif "water" in task.lower(): emoji = "💧"
                elif "timer" in task.lower(): emoji = "⏱️"
                elif "desk" in task.lower(): emoji = "🧹"
                elif "priority" in task.lower(): emoji = "📋"
                elif "goal" in task.lower(): emoji = "🎯"
                interventions.append({"priority": "high", "category": "task", "title": task, "action": task, "emoji": emoji})

        rule_based_interventions = generate_interventions(data.user_data, scores) if data.user_data else []
        if not dynamic_tasks and rule_based_interventions:
            tasks_list = "\n".join([f"- {inv.get('action', inv.get('title', 'Task'))}" for inv in rule_based_interventions[:3]])
            reply += f"\n\n**Tasks:**\n{tasks_list}"
        interventions.extend(rule_based_interventions)
        interventions = interventions[:5]

        for inv in interventions:
            memory.record_intervention(inv.get('title', ''))

        # Award XP for task completion suggestions
        if _db_manager and interventions:
            try:
                _gamification.award_xp(username, "intervention_completed")
            except Exception:
                pass

        return {
            "reply": reply,
            "analysis": analysis_result,
            "scores": scores,
            "interventions": interventions,
            "handoff_suggestion": handoff_suggestion,
            "state": {
                "detected_state": state_result.get("state"),
                "state_label": state_result.get("state_label"),
                "state_emoji": state_result.get("state_emoji"),
                "ui_mode": state_result.get("ui_mode"),
                "coaching_tone": state_result.get("coaching_tone"),
                "focus_mode": state_result.get("focus_mode"),
                "task_size": state_result.get("task_size"),
                "task_paralysis_detected": paralysis_result.get("paralysis_detected", False),
                "task_paralysis_severity": paralysis_result.get("severity", "none"),
                "microtasks": paralysis_result.get("microtasks"),
                "just_begin_offer": paralysis_result.get("just_begin_offer"),
            },
        }
    except Exception as e:
        import traceback
        logging.exception("Error in /chat endpoint")
        traceback.print_exc()
        return {"reply": f"ERROR: {str(e)}", "analysis": {"emotion": "normal", "productivity": "medium"}, "scores": {}, "interventions": []}


@app.post("/chat/stream")
def chat_stream(data: ChatRequest):
    """Streaming chat support using Server-Sent Events (SSE) and AsyncGroq."""
    # === LANGUAGE AUTO-DETECTION ===
    if data.text and len(data.text.strip()) > 1:
        try:
            import langdetect
            detected = langdetect.detect(data.text)
            if detected and len(detected) == 2:
                data.language = detected
        except Exception as e:
            logging.debug(f"Langdetect failed in /chat/stream: {e}")

    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    username = data.username or "default"
    data.text = sanitize_prompt(data.text, username)
    memory = MemoryManager(user_id=username)
    orchestrator = AgentOrchestrator(memory)
    paralysis_engine = TaskParalysisRecoveryEngine(memory)

    if _db_manager:
        memory.set_db_manager(_db_manager)
        _rag_engine.memory = memory

    current_streak = data.session_data.get('current_streak', 0) if data.session_data else 0

    async def event_generator():
        # === ROUTE TO AGENT PERSONALITY ===
        agent_id = data.agent_id or "productivity-coach"

        # === RAG: Retrieve context ===
        rag_context = _rag_engine.retrieve_context(
            username=username,
            query=data.text,
            user_data=data.user_data,
            session_data=data.session_data,
        )
        intent = _llm_router.classify_intent(data.text)
        route_instruction = _llm_router.format_response_instruction(intent)

        # Get agent context (passing agent_id)
        agent_context = orchestrator.get_context_for_prompt(data.text, current_streak, agent_id)
        agent_insights = agent_context.get("agent_insights", "")

        state_result = _state_detector.analyze(data.text, {
            "current_stress": data.user_data.get("stress_level", 5),
            "current_energy": data.user_data.get("energy_level", 5),
            "text": data.text,
        })
        state_prompt_ext = _state_detector.get_system_prompt_extension(data.text)

        coach_extension = _adaptive_coach.get_system_prompt_extension(
            data.text,
            {"current_stress": data.user_data.get("stress_level", 5)},
            data.user_data.get("mood"),
        )

        paralysis_result = paralysis_engine.process_user_message(data.text, agent_context)
        paralysis_prompt_ext = ""
        if paralysis_result["paralysis_detected"]:
            ext = paralysis_engine.get_system_prompt_extension(data.text, agent_context)
            if ext:
                paralysis_prompt_ext = ext
            memory.set_task_paralysis(True)

        # Mute ADHD/coaching insights for support-agent
        if agent_id == "support-agent":
            state_prompt_ext = ""
            coach_extension = ""
            paralysis_prompt_ext = ""

        all_context_parts = [rag_context, agent_insights, state_prompt_ext, coach_extension, paralysis_prompt_ext, route_instruction]
        all_context = "\n\n".join([p for p in all_context_parts if p])

        english_text = translate_to_english(data.text)
        analysis_result = analyze(english_text)
        scores = build_user_scores(data.user_data, text=english_text, analysis=analysis_result) if data.user_data else {}

        # ROUTE TO AGENT PERSONALITY
        agent_system_prompt = orchestrator.build_agent_specific_prompt(
            agent_id, data.text, agent_context, current_streak
        )

        instruction = "Start by warmly welcoming the user and responding directly to their input." if not data.history else f"Respond to the user as the supportive {agent_id} companion."
        if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
            instruction += "\nCRITICAL: The user has HIGH STRESS. Be extremely gentle, warm, and deeply empathetic."

        prompt = f"""
{agent_system_prompt}

{all_context}

---
Your instructions for this specific turn: {instruction}
User's current emotional state: {analysis_result['emotion']}
User's productivity level: {analysis_result['productivity']}
---

User input (Original): "{data.text}"
User input (English Translation context): "{english_text}"

CRITICAL LANGUAGE RULE: You MUST reply in the EXACT SAME language and script as "User input (Original)".
CRITICAL FORMATTING: Keep your paragraphs extremely brief (2-3 sentences max). Use formatting like bold, lists, and emojis strategically. 

You MUST format your entire response exactly like this:

REPLY:
[Your conversational, multi-paragraph response here.]

TASKS:
[1 to 3 tiny, actionable tasks. List them with a dash e.g. "- Drink water"]
"""

        full_raw_response = ""
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key:
            # Yield offline response
            offline_reply = generate_offline_reply(prompt)
            for char in offline_reply:
                yield f"data: {json.dumps({'token': char})}\n\n"
                await asyncio.sleep(0.01)
            full_raw_response = offline_reply
        else:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=groq_api_key)
                completion_stream = await client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.7,
                    max_tokens=1024,
                    stream=True,
                )
                async for chunk in completion_stream:
                    token = chunk.choices[0].delta.content
                    if token:
                        full_raw_response += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
            except Exception as e:
                logging.error(f"Error in Groq streaming: {e}")
                offline_reply = generate_offline_reply(prompt)
                for char in offline_reply:
                    yield f"data: {json.dumps({'token': char})}\n\n"
                    await asyncio.sleep(0.01)
                full_raw_response = offline_reply

        # Process post-stream computations & database persistence
        try:
            raw = full_raw_response
            reply_part = raw
            dynamic_tasks = []
            import re
            if re.search(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE):
                parts = re.split(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE)
                reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', parts[0], flags=re.IGNORECASE).strip()
                tasks_part = parts[1].strip()
                for line in tasks_part.split('\n'):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*") or line.startswith("☐"):
                        clean_task = re.sub(r'^[\-\*☐]\s*', '', line).strip()
                        if clean_task:
                            dynamic_tasks.append(clean_task)
                    else:
                        clean_line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                        if clean_line and len(clean_line) > 2:
                            dynamic_tasks.append(clean_line)
                reply_part = f"{reply_part}\n\n**Tasks:**\n{tasks_part}"
            else:
                reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', raw, flags=re.IGNORECASE).strip()

            reply = format_reply(translate_reply_if_needed(reply_part, data.language))
            handoff_suggestion = orchestrator.detect_handoff_suggestion(data.text, agent_id)

            # Record in memory
            memory.record_conversation_turn(
                user_message=data.text,
                assistant_message=reply[:500],
                interaction_type="chat",
                metadata={"language": data.language, "agent_id": agent_id}
            )
            memory.record_emotion(
                emotion=analysis_result.get("emotion", "neutral"),
                stress=scores.get("summary", {}).get("stress_level", 5),
            )

            # Database persistence
            if _db_manager:
                try:
                    _db_manager.save_chat_message(username, "user", data.text, analysis_result.get("emotion"))
                    _db_manager.save_chat_message(username, "assistant", reply[:1000])
                    _gamification.award_xp(username, "mood_checkin")
                except Exception as db_err:
                    logging.warning(f"Async stream DB error: {db_err}")

            interventions = []
            if dynamic_tasks:
                for task in dynamic_tasks[:3]:
                    emoji = "✓"
                    if "breath" in task.lower(): emoji = "🧘"
                    elif "water" in task.lower(): emoji = "💧"
                    elif "timer" in task.lower(): emoji = "⏱️"
                    elif "desk" in task.lower(): emoji = "🧹"
                    elif "priority" in task.lower(): emoji = "📋"
                    elif "goal" in task.lower(): emoji = "🎯"
                    interventions.append({"priority": "high", "category": "task", "title": task, "action": task, "emoji": emoji})

            rule_based_interventions = generate_interventions(data.user_data, scores) if data.user_data else []
            interventions.extend(rule_based_interventions)
            interventions = interventions[:5]

            for inv in interventions:
                memory.record_intervention(inv.get('title', ''))

            if _db_manager and interventions:
                try:
                    _gamification.award_xp(username, "intervention_completed")
                except Exception:
                    pass

            # Yield metadata payload
            metadata = {
                "reply": reply,
                "analysis": analysis_result,
                "scores": scores,
                "interventions": interventions,
                "handoff_suggestion": handoff_suggestion,
                "state": {
                    "detected_state": state_result.get("state"),
                    "state_label": state_result.get("state_label"),
                    "state_emoji": state_result.get("state_emoji"),
                    "ui_mode": state_result.get("ui_mode"),
                    "coaching_tone": state_result.get("coaching_tone"),
                    "focus_mode": state_result.get("focus_mode"),
                    "task_size": state_result.get("task_size"),
                    "task_paralysis_detected": paralysis_result.get("paralysis_detected", False),
                    "task_paralysis_severity": paralysis_result.get("severity", "none"),
                    "microtasks": paralysis_result.get("microtasks"),
                    "just_begin_offer": paralysis_result.get("just_begin_offer"),
                }
            }
            yield f"data: {json.dumps({'metadata': metadata})}\n\n"

        except Exception as async_err:
            logging.error(f"Error in stream post-processing: {async_err}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")



# ==================== EXISTING ENDPOINTS ====================

@app.post("/calculate_scores")
def calculate_scores(request: ScoreRequest):
    english_text = translate_to_english(request.text)
    analysis_result = analyze(english_text)
    scores = build_user_scores(request.user_data, text=english_text, adhd_answers=request.adhd_answers, analysis=analysis_result)
    interventions = generate_interventions(request.user_data, scores)
    return {"scores": scores, "interventions": interventions}

@app.post("/get_interventions")
def get_interventions_endpoint(request: InterventionRequest):
    interventions = generate_interventions(request.user_data, request.scores)
    return {"interventions": interventions}


# ==================== ANALYTICS ENDPOINTS ====================

@app.post("/analytics")
def get_analytics(data: dict):
    try:
        username = data.get("username", "default")
        user_data = data.get("user_data", {})
        force_refresh = data.get("force_refresh", False)

        # Try to read cached precompiled analytics from DB first (if not forced refresh)
        if _db_manager and not force_refresh:
            try:
                facts = _db_manager.get_facts(username, fact_type="behavior")
                for fact in facts:
                    if fact.key == "precompiled_analytics":
                        import json
                        cached_data = json.loads(fact.value)
                        # Add a flag to show this is cached
                        cached_data["cached"] = True
                        logging.info(f"Analytics: Returned cached analytics compilation for '{username}'")
                        return cached_data
            except Exception as cache_err:
                logging.warning(f"Analytics: Failed to fetch precompiled cache: {cache_err}")

        if username not in _insight_engines:
            memory = MemoryManager(user_id=username)
            _insight_engines[username] = InsightEngine(memory)
            _pattern_analyzers[username] = PatternAnalyzer(memory)
            _recommendation_engines[username] = RecommendationEngine(memory)
        insight_engine = _insight_engines[username]
        pattern_analyzer = _pattern_analyzers[username]
        rec_engine = _recommendation_engines[username]
        memory = MemoryManager(user_id=username)
        user_profile = memory.profile.data if hasattr(memory, 'profile') else {}
        insights = insight_engine.generate_insights(user_profile)
        focus_data = user_profile.get("focus_patterns", {}).get("focus_quality_trend", [])
        mood_data = user_profile.get("emotional_patterns", {}).get("mood_trend", [])
        focus_patterns = pattern_analyzer.analyze_focus_patterns(focus_data)
        mood_patterns = pattern_analyzer.analyze_mood_patterns(mood_data)
        correlations = pattern_analyzer.analyze_productivity_correlations(user_data)
        temporal = pattern_analyzer.analyze_temporal_patterns(user_data.get("activity_log", []))
        context = {"user": user_data, "session": {"current_stress": user_data.get("stress_level", 5), "current_energy": user_data.get("energy_level", 5), "current_mood": user_data.get("mood", "neutral")}}
        recommendations = rec_engine.generate_recommendations(context, user_profile)
        priority_recs = rec_engine.get_priority_recommendations(context, user_profile)
        formatted_recs = rec_engine.format_for_display(recommendations)
        insight_summary = insight_engine.get_insight_summary_text(user_profile)

        # Add DB analytics if available
        db_weekly = {}
        db_focus_hours = []
        if _db_manager:
            try:
                db_weekly = _db_manager.get_weekly_report(username)
                db_focus_hours = _db_manager.get_peak_focus_hours(username, 14)
            except Exception:
                pass

        results = {
            "insights": insights,
            "insight_summary": insight_summary,
            "focus_patterns": focus_patterns,
            "mood_patterns": mood_patterns,
            "correlations": correlations,
            "temporal_patterns": temporal,
            "recommendations": recommendations,
            "priority_recommendations": priority_recs,
            "formatted_recommendations": formatted_recs,
            "weekly_report": db_weekly,
            "peak_focus_hours": db_focus_hours,
        }

        # Cache the results in the background so next request is O(1)
        if _db_manager:
            try:
                from utils.celery_tasks import generate_analytics_task
                generate_analytics_task.delay(username, user_data)
            except Exception as task_err:
                logging.debug(f"Failed to queue background analytics cache refresh: {task_err}")

        return results
    except Exception as e:
        logging.exception(f"Analytics generation error: {e}")
        return {"insights": [], "insight_summary": "Analytics temporarily unavailable.", "focus_patterns": {}, "mood_patterns": {}, "correlations": [], "temporal_patterns": {}, "recommendations": [], "priority_recommendations": [], "formatted_recommendations": ""}


# ==================== AGENT SYSTEM ENDPOINTS ====================

@app.post("/agents/analyze")
def analyze_with_agent(request: AgentAnalyzeRequest):
    try:
        username = request.context.get("username", "default")
        memory = MemoryManager(user_id=username)
        orchestrator = AgentOrchestrator(memory)
        agent = orchestrator.get_agent(request.agent_type)
        if not agent:
            return {"success": False, "error": f"Agent '{request.agent_type}' not found", "agents_available": list(orchestrator.agents.keys())}
        context = orchestrator.get_context_for_prompt(request.context.get("message", ""), request.context.get("current_streak", 0), request.agent_type)
        analysis = agent.analyze(context, request.context)
        return {"success": True, "agent_type": request.agent_type, "analysis": analysis, "suggestions": context.get("agent_suggestions", []), "intervention": context.get("intervention")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== TASK PARALYSIS ENDPOINTS ====================

@app.post("/task-paralysis/analyze")
def analyze_task_paralysis(request: TaskParalysisRequest):
    try:
        username = request.user_data.get("username", "default")
        memory = MemoryManager(user_id=username)
        paralysis_engine = TaskParalysisRecoveryEngine(memory)
        context = memory.build_context_for_prompt()
        result = paralysis_engine.process_user_message(request.task, context)
        from task_paralysis.microtasks import MicroTaskGenerator
        micro_gen = MicroTaskGenerator()
        microtasks = micro_gen.generate_microtasks(request.task, count=5, energy_level=request.user_data.get("energy_level", 5))
        two_minute_starter = micro_gen.get_two_minute_starter(request.task)
        return {
            "task": request.task, "paralysis_detected": result["paralysis_detected"],
            "severity": result["severity"], "recovery_priority": (result.get("recovery_suggestions") or {}).get("priority", "normal"),
            "recovery_steps": (result.get("recovery_suggestions") or {}).get("steps", []),
            "microtasks": microtasks, "two_minute_starter": two_minute_starter,
            "just_begin": result.get("just_begin_offer"), "message": (result.get("recovery_suggestions") or {}).get("message", ""),
        }
    except Exception as e:
        return {"task": request.task, "paralysis_detected": False, "error": str(e), "microtasks": [], "two_minute_starter": None}


# ==================== NEW: STATE DETECTION ENDPOINT ====================

class StateDetectionRequest(BaseModel):
    text: str
    username: str = "default"
    stress_level: int = 5
    energy_level: int = 5

@app.post("/state/detect")
def detect_state(request: StateDetectionRequest):
    """Detect the user's current ADHD cognitive state."""
    try:
        context = {"current_stress": request.stress_level, "current_energy": request.energy_level, "text": request.text}
        result = _state_detector.analyze(request.text, context)
        return {
            "state": result.get("state"),
            "state_label": result.get("state_label"),
            "state_emoji": result.get("state_emoji"),
            "confidence": result.get("confidence"),
            "ui_mode": result.get("ui_mode"),
            "coaching_tone": result.get("coaching_tone"),
            "focus_mode": result.get("focus_mode"),
            "task_size": result.get("task_size"),
            "adaptations": result.get("adaptations"),
            "strategies": result.get("strategies"),
            "is_crisis": result.get("is_crisis", False),
        }
    except Exception as e:
        return {"error": str(e)}


# ==================== NEW: FOCUS ENGINE ENDPOINTS ====================

@app.post("/focus/recommend")
def recommend_focus(request: FocusRecommendRequest):
    """Get a personalized focus session recommendation."""
    try:
        result = _focus_engine.recommend_session(
            mode_id=request.mode_id, focus_score=request.focus_score,
            sessions_completed_today=request.sessions_completed_today,
            stress_level=request.stress_level, energy_level=request.energy_level,
            fatigue=request.fatigue,
        )
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/focus/distraction-log")
def log_distraction(data: dict):
    """Log a distraction event for pattern analysis."""
    username = data.get("username", "default")
    distraction = data.get("distraction", "")
    category = data.get("category", "other")
    energy_level = data.get("energy_level")
    try:
        _focus_engine.log_distraction(username, distraction, category, energy_level)
        if _db_manager:
            try:
                _gamification.award_xp(username, "focus_mode_used")
            except Exception:
                pass
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/focus/complete")
def complete_focus_session(data: dict):
    """Record a completed focus session and award XP."""
    username = data.get("username", "default")
    mode = data.get("mode", "standard")
    duration = data.get("duration_minutes", 25)
    quality = data.get("quality")
    completed = data.get("completed", True)
    try:
        if _db_manager:
            _db_manager.save_focus_session(username, mode, duration, completed, quality)
            _gamification.award_xp(username, "focus_session_completed")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/focus/distraction-patterns")
def get_distraction_patterns(data: dict):
    """Get distraction pattern analysis."""
    username = data.get("username", "default")
    days = data.get("days", 7)
    try:
        patterns = _focus_engine.get_distraction_patterns(username, days)
        return patterns
    except Exception as e:
        return {"error": str(e)}


# ==================== NEW: GAMIFICATION ENDPOINTS ====================

@app.get("/gamification/{username}")
def get_gamification_state(username: str):
    """Get complete gamification state for a user."""
    try:
        if not _db_manager:
            return {"error": "Database not available"}
        state = _gamification.get_full_state(username)
        return state
    except Exception as e:
        return {"error": str(e)}

@app.post("/gamification/award-xp")
def award_xp_endpoint(data: dict):
    """Award XP for a specific action."""
    username = data.get("username", "default")
    action = data.get("action", "")
    if not action:
        return {"success": False, "error": "Action required"}
    try:
        if not _db_manager:
            return {"success": False, "error": "Database not available"}
        result = _gamification.award_xp(username, action)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/gamification/{username}/achievements")
def get_achievements(username: str):
    """Get all achievements for a user."""
    try:
        if not _db_manager:
            return {"error": "Database not available"}
        return {"achievements": _db_manager.get_achievements(username)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/gamification/{username}/skills")
def get_skills(username: str):
    """Get all skill progress for a user."""
    try:
        if not _db_manager:
            return {"error": "Database not available"}
        return {"skills": _db_manager.get_skills(username)}
    except Exception as e:
        return {"error": str(e)}


# ==================== NEW: MOOD TRACKING ENDPOINTS ====================

class MoodLogRequest(BaseModel):
    username: str
    mood: str
    emoji: str = ""
    energy: int = 5
    focus: int = 5
    burnout: int = 0
    anxiety: int = 0
    productivity: int = 5
    note: str = ""

@app.post("/mood/log")
def log_mood(request: MoodLogRequest):
    """Log a mood entry and award XP."""
    try:
        if _db_manager:
            entry = _db_manager.save_mood(
                request.username, request.mood, request.emoji,
                request.energy, request.focus, request.burnout,
                request.anxiety, request.productivity, request.note,
            )
            if entry:
                _gamification.award_xp(request.username, "mood_checkin")
                return {"success": True, "entry_id": entry.id}
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/mood/{username}")
def get_mood_history(username: str, days: int = 30):
    """Get mood history for a user."""
    try:
        if not _db_manager:
            return {"error": "Database not available"}
        entries = _db_manager.get_mood_history(username, days)
        summary = _db_manager.get_mood_summary(username, days)
        burnout_alert = _db_manager.detect_burnout_alert(username)
        return {
            "entries": [{"mood": e.mood, "emoji": e.emoji, "energy": e.energy, "focus": e.focus, "burnout": e.burnout, "anxiety": e.anxiety, "note": e.note, "created_at": e.created_at.isoformat()} for e in entries],
            "summary": summary,
            "burnout_alert": burnout_alert,
        }
    except Exception as e:
        return {"error": str(e)}


# ==================== NEW: INTERVENTION LOGGING ====================

@app.post("/interventions/complete")
def complete_intervention(data: dict):
    """Record an intervention completion."""
    username = data.get("username", "default")
    intervention_type = data.get("type", "general")
    title = data.get("title", "")
    duration = data.get("duration_minutes")
    try:
        if _db_manager:
            _db_manager.record_intervention(username, intervention_type, title, duration)
            _gamification.award_xp(username, "intervention_completed")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== NEW: WEEKLY REPORT ====================

@app.get("/report/weekly/{username}")
def get_weekly_report(username: str):
    """Get comprehensive weekly report."""
    try:
        if not _db_manager:
            return {"error": "Database not available"}
        report = _db_manager.get_weekly_report(username)
        # Add gamification context
        game_state = _gamification.get_full_state(username)
        report["gamification"] = game_state
        return report
    except Exception as e:
        return {"error": str(e)}


# ==================== NEW: DASHBOARD SUMMARY ====================

@app.get("/dashboard/{username}")
def get_dashboard(username: str):
    """Get comprehensive dashboard data."""
    try:
        result = {"scores": {}, "mood": {}, "focus": {}, "streaks": {}, "gamification": {}, "state": {}}
        if _db_manager:
            daily = _db_manager.get_daily_summary(username)
            result["daily"] = daily
            result["streaks"] = _db_manager.get_all_streak_summary(username)
            result["mood"] = _db_manager.get_mood_summary(username, 7)
            result["focus"] = _db_manager.get_focus_stats(username, 7)
        # Get emotion context from memory
        memory = MemoryManager(user_id=username)
        context = memory.build_context_for_prompt()
        result["session"] = context.get("session", {})
        # Get latest state
        result["state"] = _state_detector.get_current_state_summary()
        return result
    except Exception as e:
        return {"error": str(e)}


# ==================== MEMORY ENDPOINTS ====================

@app.get("/memory/{username}")
def get_memory_context(username: str):
    try:
        memory = MemoryManager(user_id=username)
        context = memory.build_context_for_prompt()
        stats = memory.get_stats()
        prompt_context = memory.get_context_for_prompt_text()
        return {"username": username, "context": context, "stats": stats, "prompt_context": prompt_context}
    except Exception as e:
        return {"username": username, "error": str(e), "context": {}, "stats": {}, "prompt_context": "Memory temporarily unavailable."}

@app.post("/memory/{username}/search")
def search_memory(username: str, request: dict):
    try:
        query = request.get("query", "")
        n_results = request.get("n_results", 5)
        memory = MemoryManager(user_id=username)
        results = memory.search_memories(query, n_results=n_results)
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": str(e), "results": []}

@app.post("/memory/{username}/record")
def record_memory_event(username: str, request: dict):
    try:
        memory = MemoryManager(user_id=username)
        event_type = request.get("type", "manual")
        content = request.get("content", "")
        metadata = request.get("metadata", {})
        if event_type == "emotion":
            memory.record_emotion(emotion=metadata.get("emotion", "neutral"), stress=metadata.get("stress", 5), energy=metadata.get("energy"))
        elif event_type == "focus":
            memory.record_focus_session(duration_minutes=metadata.get("duration", 25), quality=metadata.get("quality", 5), hour=metadata.get("hour", 12))
        elif event_type == "task":
            memory.record_task_added(content, source=metadata.get("source", "manual"))
        elif event_type == "task_completed":
            memory.record_task_completed(content, difficulty=metadata.get("difficulty", 5))
        elif event_type == "procrastination":
            memory.record_procrastination_trigger(content, metadata.get("context", ""))
        return {"success": True, "event_type": event_type}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "models_loaded": {
            "adhd": adhd_inference is not None,
            "productivity": productivity_inference is not None,
            "student": student_inference is not None,
            "mental_health": mental_pipeline is not None,
        },
        "database": _db_manager is not None,
        "features": {
            "rag": True,
            "gamification": True,
            "state_detection": True,
            "adaptive_coach": True,
            "focus_engine": True,
            "fact_extraction": True,
        },
    }


# ==================== FEEDBACK & SUPPORT ====================

class FeedbackRequest(BaseModel):
    username: str
    rating: int
    category: str
    feedback_text: Optional[str] = None

class SupportTicketRequest(BaseModel):
    username: str
    type: str
    subject: str
    description: str

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Save feedback
    feedback = _db_manager.save_feedback(
        username=request.username,
        rating=request.rating,
        category=request.category,
        feedback_text=request.feedback_text
    )
    if not feedback:
        raise HTTPException(status_code=400, detail="Failed to save feedback. User not found.")
    
    # Award 15 XP to consistency skill
    xp_result = _db_manager.add_xp(request.username, 15, "consistency")
    
    # Check if achievements unlocked
    new_achievements = _db_manager.check_and_award_achievements(request.username)
    new_ach_list = [
        {
            "id": a.achievement_id,
            "title": a.title,
            "description": a.description,
            "xp_reward": a.xp_reward
        }
        for a in new_achievements
    ]
    
    return {
        "success": True,
        "message": "Feedback submitted successfully!",
        "xp_awarded": 15,
        "skill_status": xp_result,
        "new_achievements": new_ach_list
    }

@app.post("/support/ticket")
def submit_support_ticket(request: SupportTicketRequest):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    ticket = _db_manager.save_support_ticket(
        username=request.username,
        type=request.type,
        subject=request.subject,
        description=request.description
    )
    if not ticket:
        raise HTTPException(status_code=400, detail="Failed to save ticket. User not found.")
        
    return {
        "success": True,
        "message": "Support ticket created successfully!",
        "ticket": {
            "id": ticket.id,
            "type": ticket.type,
            "subject": ticket.subject,
            "description": ticket.description,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat()
        }
    }

@app.get("/support/faqs")
def get_support_faqs():
    # Curated shame-free ADHD coping FAQs
    return [
        {
            "id": "faq-paralysis",
            "question": "🌪️ How do I overcome sudden task paralysis?",
            "answer": "When task paralysis strikes, your brain is treating the threat of starting a task like a literal physical danger. Don't fight it! Give yourself absolute permission to do the task badly or do just *one single detail* for 2 minutes. Start a micro-timer, and if you want to stop after 2 minutes, you have fully succeeded."
        },
        {
            "id": "faq-hyperfocus",
            "question": "🌀 Help, I am stuck in an intense hyperfocus spiral!",
            "answer": "Hyperfocus is a powerful ADHD gift, but it can drain your body. Transitioning out is hard. Use a transitional bridge: instead of stopping immediately, tell yourself you will stop in 5 minutes, stand up and stretch without looking away, then grab a glass of water. A change of physical state helps reset the brain."
        },
        {
            "id": "faq-blindness",
            "question": "⏳ How can I handle time blindness during work?",
            "answer": "ADHD brains perceive time as 'Now' or 'Not Now'. To make time visible, use visual timers (like the standard countdown visual arc in our Focus page) rather than digital numbers. Set soft, chime-based alarms 5 minutes *before* you actually need to transition to prevent jump-scares."
        },
        {
            "id": "faq-burnout",
            "question": "🔋 What is an ADHD shutdown, and how do I recover?",
            "answer": "When you have overstimulated or pushed your brain too hard, it goes into a power-saving mode (shutdown/burnout). This is a physical necessity. Rest shame-free. Lie down in a dark or quiet room, drink some hydration, and avoid complex decision-making for at least 1-2 hours."
        },
        {
            "id": "faq-glitch",
            "question": "🐛 What if the coach or the app glitches?",
            "answer": "No worries! This is a shame-free technical zone. Simply submit a glitch report on the left panel. Include a tiny description of what happened. Our support bots will log it, clean up the SQLite files, and restart the cache to get you focused again."
        }
    ]


class TicketStatusUpdateRequest(BaseModel):
    status: str


@app.get("/support/tickets/{username}")
def get_user_tickets(username: str):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    tickets = _db_manager.get_user_support_tickets(username)
    return {
        "success": True,
        "tickets": [
            {
                "id": t.id,
                "type": t.type,
                "subject": t.subject,
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in tickets
        ]
    }


@app.get("/admin/feedbacks")
def get_admin_feedbacks(current_admin: str = Depends(require_admin)):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    from src.database.models import UserFeedback, User
    db = _db_manager.db
    results = db.query(UserFeedback, User.username).join(User, UserFeedback.user_id == User.id).order_by(UserFeedback.created_at.desc()).all()
    feedbacks = []
    for fb, username in results:
        feedbacks.append({
            "id": fb.id,
            "username": username,
            "rating": fb.rating,
            "category": fb.category,
            "feedback_text": fb.feedback_text,
            "created_at": fb.created_at.isoformat()
        })
        
    # Security Audit Log
    from src.utils.audit_logger import audit_log
    audit_log(
        username=current_admin,
        action="view_admin_feedbacks",
        status="SUCCESS"
    )
    
    return {"success": True, "feedbacks": feedbacks}


@app.get("/admin/tickets")
def get_admin_tickets(current_admin: str = Depends(require_admin)):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    from src.database.models import SupportTicket, User
    db = _db_manager.db
    results = db.query(SupportTicket, User.username).join(User, SupportTicket.user_id == User.id).order_by(SupportTicket.created_at.desc()).all()
    tickets = []
    for t, username in results:
        tickets.append({
            "id": t.id,
            "username": username,
            "type": t.type,
            "subject": t.subject,
            "description": t.description,
            "status": t.status,
            "created_at": t.created_at.isoformat()
        })
        
    # Security Audit Log
    from src.utils.audit_logger import audit_log
    audit_log(
        username=current_admin,
        action="view_admin_tickets",
        status="SUCCESS"
    )
    
    return {"success": True, "tickets": tickets}


@app.put("/admin/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, request: TicketStatusUpdateRequest, current_admin: str = Depends(require_admin)):
    if not _db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    from src.database.models import SupportTicket
    db = _db_manager.db
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    old_status = ticket.status
    ticket.status = request.status
    db.commit()
    
    # Transaction Audit Log
    from src.utils.audit_logger import audit_log
    audit_log(
        username=current_admin,
        action="update_ticket_status",
        status="SUCCESS",
        details={"ticket_id": ticket_id, "old_status": old_status, "new_status": request.status}
    )
    
    return {
        "success": True,
        "message": f"Ticket status successfully updated to {request.status}",
        "ticket": {
            "id": ticket.id,
            "status": ticket.status
        }
    }

# ==================== BACKGROUND TASK SYSTEM ENDPOINTS ====================

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

@app.post("/tasks/calculate_scores")
def calculate_scores_async(request: ScoreRequest, async_task: bool = True, username: str = "default"):
    """
    Triggers heavy ML model inference asynchronously in Celery.
    If async_task=False, runs synchronously and returns results immediately.
    """
    if not async_task:
        # Run synchronously for backward compatibility and tests
        return calculate_scores(request)
        
    try:
        from utils.celery_tasks import calculate_ml_scores_task
        task = calculate_ml_scores_task.delay(
            request.user_data,
            request.text,
            request.adhd_answers,
            username
        )
        from utils.celery_app import celery_app
        if getattr(celery_app.conf, "task_always_eager", False):
            EAGER_TASK_RESULTS[task.id] = task.result
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        # Fallback to sync if Celery fails to queue
        logging.warning(f"Failed to queue task, running synchronously: {e}")
        return calculate_scores(request)

@app.post("/tasks/analytics")
def generate_analytics_async(request: dict):
    """
    Triggers analytics calculation task in the background.
    """
    username = request.get("username", "default")
    user_data = request.get("user_data", {})
    try:
        from utils.celery_tasks import generate_analytics_task
        task = generate_analytics_task.delay(username, user_data)
        from utils.celery_app import celery_app
        if getattr(celery_app.conf, "task_always_eager", False):
            EAGER_TASK_RESULTS[task.id] = task.result
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@app.post("/tasks/synthesize_personality")
def synthesize_personality_async(request: dict):
    """
    Triggers multi-agent personality synthesis task in the background.
    """
    username = request.get("username", "default")
    try:
        from utils.celery_tasks import synthesize_personality_task
        task = synthesize_personality_task.delay(username)
        from utils.celery_app import celery_app
        if getattr(celery_app.conf, "task_always_eager", False):
            EAGER_TASK_RESULTS[task.id] = task.result
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@app.post("/tasks/compile_context")
def compile_context_async(request: dict):
    """
    Triggers long-running context compilation task in the background.
    """
    username = request.get("username", "default")
    try:
        from utils.celery_tasks import compile_context_task
        task = compile_context_task.delay(username)
        from utils.celery_app import celery_app
        if getattr(celery_app.conf, "task_always_eager", False):
            EAGER_TASK_RESULTS[task.id] = task.result
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@app.get("/tasks/status/{task_id}")
def get_task_status(task_id: str):
    """
    Retrieves the status and results of an asynchronous task.
    """
    if task_id in EAGER_TASK_RESULTS:
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": EAGER_TASK_RESULTS[task_id],
            "error": None
        }
    try:
        from utils.celery_app import celery_app
        res = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": res.status,
            "result": None,
            "error": None
        }
        
        if res.status == "SUCCESS":
            response["result"] = res.result
        elif res.status == "FAILURE":
            response["error"] = str(res.result)
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main_api:app", host="0.0.0.0", port=8000, reload=True)


