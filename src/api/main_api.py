import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import requests
from functools import lru_cache
import threading
from fastapi import FastAPI
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

# Logging is now configured at the application entry point (frontend/app.py)
# to ensure it's set up correctly for the cloud environment.
app = FastAPI(title="ADHD Productivity API")

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
You are an empathetic, dynamic, and highly engaging ADHD productivity coach. Your goal is to be a supportive friend and an effective guide, adapting your advice to the user's unique situation.

**STRICT COACHING RULES:**
1. **BE DYNAMIC & CONVERSATIONAL:** Never reply with just one short sentence. Provide a thoughtful, warm, and engaging response. Acknowledge the user's feelings and situation thoroughly but concisely.
2. **USE SHORT PARAGRAPHS:** Avoid massive walls of text, but do write a few short, visually spaced paragraphs. Use emojis to keep it highly readable and friendly.
3. **HUMAN TONE:** Be warm, encouraging, and natural. Speak like a real friend or mentor who is actively listening.
4. **GUIDE WITH A QUESTION:** Always end your conversational reply with ONE clear, engaging question to prompt the user's next thought or action.
5. **ACTIONABLE ADVICE (TASKS):** You MUST ALWAYS provide 1 to 3 tiny, actionable micro-steps in the dedicated TASKS section, EVEN for simple greetings like "hi".

**Example Format:**

REPLY:
Hey! It makes total sense that you're feeling overwhelmed right now. 🌪️ 

Sometimes the hardest part is just figuring out where to start when everything feels like too much. But don't worry, we've got this together!

What is the absolute smallest thing you could tackle first today? 🤔

TASKS:
- 🧹 Clear one small corner of your desk.
- ⏱️ Set a timer for just 5 minutes.
- 💧 Drink a glass of water.
"""


class ChatRequest(BaseModel):
    text: str
    history: List[Any] = Field(default_factory=list)
    user_data: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    language_name: str = "English"


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

    depression_pct = estimate_depression_health_score(user_snapshot, engineered_df)

    mental_health_probability = predict_mental_health_probability(text)
    if mental_health_probability is not None:
        mental_health_pct = float(mental_health_score(mental_health_probability))
        # Real-time perturbation: adjust static ML outputs based on current chat sentiment
        final_adhd_risk = min(1.0, final_adhd_risk + (mental_health_probability * 0.3))
        productivity_pct = max(0.0, productivity_pct - (mental_health_probability * 40.0))
        depression_pct = (depression_pct * 0.6) + (mental_health_pct * 0.4)
    else:
        mental_health_pct = float(max(0, min(100, 100 - (calculated_stress * 10))))

    # Strongly force variance based on analyzed text labels
    if analysis:
        emotion = analysis.get("emotion", "neutral")
        prod = analysis.get("productivity", "medium")

        if emotion == "stress":
            final_adhd_risk = min(1.0, final_adhd_risk + 0.35)
            depression_pct = max(0.0, depression_pct - 30.0) # lower score means higher depression risk
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
    import json
    import re
    try:
        # 1. Try robust LLM zero-shot classification first
        prompt = f"""Analyze the following text from a user seeking productivity and mental health coaching. Classify the user's emotion as exactly one of: 'positive', 'neutral', or 'stress'. Classify their productivity status as exactly one of: 'high', 'medium', or 'low'. Respond with ONLY a valid JSON object in this format: {{"emotion": "...", "productivity": "..."}}. Do not include any other text. Text to analyze: '{text}'"""
        raw_response = get_ai_reply(prompt)
        match = re.search(r'\{.*\}', raw_response.replace('\n', ' '), re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "emotion": result.get("emotion", "neutral").lower(),
                "productivity": result.get("productivity", "medium").lower()
            }
    except Exception as e:
        logging.debug(f"LLM analysis failed, falling back to heuristics: {e}")

    # 2. Fallback to heuristics and local ML
    try:
        predicted_probability = predict_mental_health_probability(text)
        prompt_lower = text.lower()
        
        # Analyze emotion
        if any(keyword in prompt_lower for keyword in POSITIVE_KEYWORDS):
            emotion_label = "positive"
        elif predicted_probability is None:
            if any(keyword in prompt_lower for keyword in STRESS_KEYWORDS):
                emotion_label = "stress"
            else:
                emotion_label = "neutral"
        else:
            if predicted_probability >= 0.25 or any(keyword in prompt_lower for keyword in STRESS_KEYWORDS):
                emotion_label = "stress"
            else:
                emotion_label = "neutral"

        # Analyze productivity
        if any(keyword in prompt_lower for keyword in PRODUCTIVE_KEYWORDS):
            productivity = "high"
        elif any(keyword in prompt_lower for keyword in UNPRODUCTIVE_KEYWORDS):
            productivity = "low"
        else:
            productivity = "medium"

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


def build_prompt(
    user_input: str,
    english_translation: str,
    analysis: Dict[str, Any],
    history: List[Any],
    scores: Dict[str, Any] = None,
    language: str = "en",
    language_name: str = "English",
):
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
"""

    if not history:
        instruction = "Start by warmly welcoming the user and responding directly to their input. Provide a thoughtful, engaging, and dynamic response spanning a few short paragraphs. Use emojis and bullet points to make it visually appealing, and end with a single, gentle guiding question."
    else:
        instruction = "Respond to the user as a supportive, dynamic friend. Give a thoughtful and empathetic reply, acknowledge their progress or struggles in a few short paragraphs, provide actionable but small advice using bullet points, and end with an engaging question to keep the conversation flowing."

    if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
        instruction += "\nCRITICAL: The user has HIGH STRESS. Be extremely gentle, warm, and deeply empathetic. Focus on emotional support rather than pushing productivity right now."

    prompt = f"""
{SYSTEM_PROMPT}

{context}

---
Your instructions for this specific turn: {instruction}
---

User input (Original): "{user_input}"
User input (English Translation context): "{english_translation}"

CRITICAL LANGUAGE RULE: You MUST reply in the EXACT SAME language and script as "User input (Original)". If it is transliterated (e.g. "ela unnav"), reply in the same transliterated language. Do NOT reply in Catalan, Spanish, or other unrelated languages.
CRITICAL FORMATTING: Avoid long paragraphs at all costs. Format your advice using short bullet points and a mix of emojis. End with a single question.

You MUST format your entire response exactly like this:

REPLY:
[Your conversational, multi-paragraph response here. Empathize and ask your ONE guiding question. DO NOT include any task lists or bullet points of tasks here.]

TASKS:
[You MUST ALWAYS provide 1 to 3 tiny, actionable tasks, EVEN IF the user just says "hi" or asks a question. Suggest small grounding steps if no specific task is discussed. List them with a dash e.g. "- Drink water"]
"""

    return prompt

def translate_to_english(text: str) -> str:
    """Translates any non-English text to English for accurate NLP and ML processing."""
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
        logging.debug("Reply translation failed; returning original reply", exc_info=True)
        return reply


def generate_offline_reply(prompt):
    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["focus", "distract", "attention", "overwhelm", "concentration"]):
        reply = (
            "REPLY:\nHey there! It sounds like you're feeling pretty overwhelmed right now, which makes focusing incredibly difficult. That's completely normal and okay! 🌬️\n\nSometimes our brains just need a tiny reset before diving back in. Let's take it slow and try not to force it.\n\nIf we could pick just *one* super tiny thing to knock out right now, what would it be? 🤔\n\n"
            "TASKS:\n- Take 3 deep breaths\n- Open your notes\n- Start a 5-minute timer"
        )
    elif any(keyword in prompt_lower for keyword in ["time", "schedule", "plan", "deadline", "routine"]):
        reply = (
            "REPLY:\nPlanning can definitely be tricky, especially when there's so much on your plate! 🗓️\n\nInstead of looking at the whole schedule and getting stressed, let's just zoom in on right now.\n\nWhat is the very next thing you need to do in the next 10 minutes to feel a little better? ⏳\n\n"
            "TASKS:\n- List top 3 priorities\n- Pick the easiest one\n- Block out 15 minutes"
        )
    elif any(keyword in prompt_lower for keyword in ["motivation", "procrast", "lazy", "energy"]):
        reply = (
            "REPLY:\nIt's totally normal to hit a wall with motivation. We all have those days where our energy is just completely zapped! 🔋\n\nSometimes starting is the hardest part. What if we just do a 2-minute 'starter' task to build a tiny bit of momentum?\n\nWhat's the absolute smallest possible step you could take right now? ✨\n\n"
            "TASKS:\n- Drink a glass of water\n- Clear your desk space\n- Do a 2-minute starter task"
        )
    else:
        reply = (
            "REPLY:\nI hear you, and I completely understand where you're coming from. I'm right here to support you! 🤝\n\nLet's figure this out together step by step so it doesn't feel like too much.\n\nWhat is the main thing you want us to tackle together today? 🚀\n\n"
            "TASKS:\n- Define your main goal for today\n- Break it into 3 small steps\n- Start the first step"
        )

    return reply

# Queueing mechanism to prevent slowing down under load
# Limits how many concurrent LLM generations can happen at once
MAX_CONCURRENT_AI_REQUESTS = int(os.getenv("MAX_CONCURRENT_AI_REQUESTS", "4"))
ai_queue_semaphore = threading.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

@lru_cache(maxsize=1000)
def get_ai_reply(prompt, language: str = "en"):
    # Wait up to 15 seconds in the queue before gracefully degrading
    acquired = ai_queue_semaphore.acquire(timeout=15.0)
    if not acquired:
        logging.warning("AI Request queue is full and timed out. Using offline fallback.")
        return generate_offline_reply(prompt)

    try:
        # 1. Try Groq Cloud API (For Live Render Deployment)
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
            
        # 2. Fallback to Local Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        res = requests.post(
            ollama_url,
            json={
                "model": "llama3:instruct",
                "prompt": prompt,
                "stream": False
            },
            timeout=60  # Increased to give local Ollama time to respond, especially on first load
        )
        res.raise_for_status()
        return res.json().get("response", "")
    except requests.exceptions.Timeout:
        logging.error("Ollama request timed out")
        return generate_offline_reply(prompt)
    except requests.exceptions.RequestException as exc:
        logging.error("AI API request failed: %s", exc)
        return generate_offline_reply(prompt)
    except Exception:
        logging.exception("Unexpected error generating AI reply")
        return generate_offline_reply(prompt)
    finally:
        ai_queue_semaphore.release()


def format_reply(reply):
    return reply.strip()


@app.post("/chat")
def chat(data: ChatRequest):
    try:
        english_text = translate_to_english(data.text)
        analysis = analyze(english_text)
        scores = build_user_scores(data.user_data, text=english_text, analysis=analysis) if data.user_data else {}
        prompt = build_prompt(data.text, english_text, analysis, data.history, scores, data.language, data.language_name)
        raw = get_ai_reply(prompt, data.language)
        
        reply_part = raw
        dynamic_tasks = []
        
        import re
        if re.search(r'\bTASKS\s*[:\-]', raw, flags=re.IGNORECASE):
            parts = re.split(r'\bTASKS\s*[:\-]', raw, flags=re.IGNORECASE)
            reply_part = re.sub(r'^REPLY\s*[:\-]*\s*', '', parts[0], flags=re.IGNORECASE).strip()
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
            
            # Format the reply to natively include tasks and the reminder to tick checkboxes
            reply_part = f"{reply_part}\n\n**Tasks:**\n{tasks_part}\n\n*(If you complete any of these tasks, please tick the checkbox in the sidebar!)*"
        else:
            reply_part = re.sub(r'^REPLY\s*[:\-]*\s*', '', raw, flags=re.IGNORECASE).strip()
            
        reply = format_reply(translate_reply_if_needed(reply_part, data.language))

        interventions = []
        if dynamic_tasks:
            # Create interventions for each task without appending to reply
            # (reply will be formatted separately in frontend)
            for task in dynamic_tasks[:3]:
                # Extract emoji if present or assign based on task keywords
                emoji = "✓"
                if "breath" in task.lower():
                    emoji = "🧘"
                elif "water" in task.lower():
                    emoji = "💧"
                elif "timer" in task.lower():
                    emoji = "⏱️"
                elif "desk" in task.lower():
                    emoji = "🧹"
                elif "priority" in task.lower():
                    emoji = "📋"
                elif "goal" in task.lower():
                    emoji = "🎯"
                
                interventions.append({
                    "priority": "high",
                    "category": "task",
                    "title": task,
                    "action": task,
                    "emoji": emoji
                })

        rule_based_interventions = generate_interventions(data.user_data, scores) if data.user_data else []
        
        # If the AI omitted tasks (e.g. returned a 1-line reply), fallback to injecting AI-suggested rule-based tasks natively into the chat reply
        if not dynamic_tasks and rule_based_interventions:
            tasks_list_text = "\n".join([f"- {inv.get('action', inv.get('title', 'Task'))}" for inv in rule_based_interventions[:3]])
            fallback_tasks_text = f"\n\n**Tasks:**\n{tasks_list_text}\n\n*(If you complete any of these tasks, please tick the checkbox in the sidebar!)*"
            
            if data.language and not data.language.startswith("en"):
                fallback_tasks_text = translate_reply_if_needed(fallback_tasks_text, data.language)
                
            reply += fallback_tasks_text

        interventions.extend(rule_based_interventions)
        interventions = interventions[:5]

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
    english_text = translate_to_english(request.text)
    analysis = analyze(english_text)
    scores = build_user_scores(
        request.user_data,
        text=english_text,
        adhd_answers=request.adhd_answers,
        analysis=analysis
    )
    interventions = generate_interventions(request.user_data, scores)
    return {"scores": scores, "interventions": interventions}


@app.post("/get_interventions")
def get_interventions_endpoint(request: InterventionRequest):
    interventions = generate_interventions(request.user_data, request.scores)
    return {"interventions": interventions}
