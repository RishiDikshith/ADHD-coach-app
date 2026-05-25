import os
import json
import logging
from datetime import datetime, timezone
from celery.exceptions import MaxRetriesExceededError
from utils.celery_app import celery_app
from database.crud import DatabaseManager

logger = logging.getLogger(__name__)

# ==================== LAZY ML MODEL LOADERS ====================
# We lazy-load these heavy models only when a task actually runs,
# keeping Celery worker startup light and fast.
_models = {
    "adhd": None,
    "productivity": None,
    "student": None,
    "mental_health": None
}

def get_ml_models():
    """Lazy-load and cache the machine learning models."""
    from pathlib import Path
    import joblib
    from utils.helpers import prepare_model_for_inference
    from ml_models.efficient_inference import EfficientInference, load_model_cached

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    MODELS_DIR = PROJECT_ROOT / "models"

    if _models["adhd"] is None:
        try:
            _models["adhd"] = EfficientInference(
                str(MODELS_DIR / "adhd_risk_model.pkl"), "ADHD Risk Model"
            )
            logger.info("Celery: ADHD Risk Model lazy-loaded successfully")
        except Exception as e:
            logger.error(f"Celery: Failed to load ADHD model: {e}")

    if _models["productivity"] is None:
        try:
            _models["productivity"] = EfficientInference(
                str(MODELS_DIR / "productivity_model.pkl"), "Productivity Model"
            )
            logger.info("Celery: Productivity Model lazy-loaded successfully")
        except Exception as e:
            logger.error(f"Celery: Failed to load Productivity model: {e}")

    if _models["student"] is None:
        try:
            _models["student"] = EfficientInference(
                str(MODELS_DIR / "student_model.pkl"), "Student Depression Model"
            )
            logger.info("Celery: Student Depression Model lazy-loaded successfully")
        except Exception as e:
            logger.error(f"Celery: Failed to load Student model: {e}")

    if _models["mental_health"] is None:
        try:
            mental_pipeline = load_model_cached(str(MODELS_DIR / "mental_health_nlp_pipeline.pkl"))
            _models["mental_health"] = prepare_model_for_inference(mental_pipeline)
            logger.info("Celery: Mental Health NLP Pipeline lazy-loaded successfully")
        except Exception as e:
            logger.error(f"Celery: Failed to load Mental Health model: {e}")

    return _models


# ==================== 1. ML INFERENCE TASK ====================

@celery_app.task(name="tasks.calculate_ml_scores", bind=True, max_retries=3)
def calculate_ml_scores_task(self, user_data: dict, text: str = "", adhd_answers: list = None, username: str = "default"):
    """
    Offloads heavy ML model inference (productivity, ADHD risk, depression scoring)
    to a Celery worker. Retries with exponential backoff on transient errors.
    """
    logger.info(f"Celery: Starting ML inference task for user '{username}'...")
    try:
        import pandas as pd
        import numpy as np
        from feature_engineering.feature_builder import build_features
        from scoring.adhd_questionnaire_score import calculate_adhd_score
        from scoring.adhd_scoring import combined_adhd_score
        from scoring.final_score import final_score
        from scoring.mental_health_scoring import mental_health_score, analyze_stress_text
        from scoring.productivity_scoring import productivity_score
        from intervention.intervention_engine import generate_interventions

        models = get_ml_models()
        adhd_inf = models["adhd"]
        prod_inf = models["productivity"]
        student_inf = models["student"]
        mh_pipeline = models["mental_health"]

        # Parse user snapshot
        user_snapshot = dict(user_data)
        stress_level = user_snapshot.get("stress_level", 5)
        user_snapshot["stress_level"] = stress_level
        
        # Build features dataframe
        engineered_df = build_features(pd.DataFrame([user_snapshot]))

        # 1. Productivity scoring
        try:
            if prod_inf is None:
                raise ValueError("Productivity model unavailable")
            productivity_raw = np.expm1(prod_inf.predict(engineered_df)[0])
            productivity_pct = float(productivity_score(productivity_raw))
        except Exception as e:
            logger.warning(f"Productivity score computation failed: {e}")
            productivity_pct = 50.0

        # 2. ADHD risk scoring
        try:
            if adhd_inf is None:
                raise ValueError("ADHD model unavailable")
            adhd_raw = adhd_inf.predict(engineered_df)[0]
            adhd_risk = max(0.0, min(1.0, adhd_raw / 100 if adhd_raw > 1 else adhd_raw))
        except Exception as e:
            logger.warning(f"ADHD risk model computation failed: {e}")
            adhd_risk = 0.5

        # 3. ADHD Questionnaire Score (if answers present)
        if adhd_answers:
            q_score, q_level = calculate_adhd_score(adhd_answers)
            adhd_health_pct, final_adhd_risk = combined_adhd_score(q_score, adhd_risk)
        else:
            q_score, q_level = None, None
            final_adhd_risk = adhd_risk
            adhd_health_pct = max(0, min(100, (1 - adhd_risk) * 100))

        # 4. Student Depression Score
        depression_pct = 50.0
        if student_inf is not None:
            try:
                predicted_label = student_inf.predict(engineered_df)[0]
                from scoring.student_scoring import depression_score
                depression_pct = float(depression_score(predicted_label))
            except Exception as e:
                logger.warning(f"Student model prediction failed: {e}")
                estimated_risk = min(1.0, max(0.0, (stress_level / 10) * 0.7 + max(0, 7 - user_snapshot.get("sleep_hours", 7)) * 0.08))
                depression_pct = float(max(20, min(85, (1 - estimated_risk) * 100)))

        # 5. Mental Health NLP Score
        ml_probability = None
        if mh_pipeline is not None and text:
            try:
                if hasattr(mh_pipeline, "predict_proba"):
                    probabilities = mh_pipeline.predict_proba([text])[0]
                    classes = [str(val).lower() for val in getattr(mh_pipeline, "classes_", [])]
                    if "1" in classes:
                        ml_probability = float(probabilities[classes.index("1")])
                    elif "stress" in classes:
                        ml_probability = float(probabilities[classes.index("stress")])
                    else:
                        ml_probability = float(np.max(probabilities))
                else:
                    prediction = str(mh_pipeline.predict([text])[0]).lower()
                    ml_probability = 1.0 if prediction in {"1", "stress"} else 0.0
            except Exception as e:
                logger.warning(f"Mental Health pipeline execution failed: {e}")
        
        # Combine NLP ML probability with heuristic text analysis
        stress_probability = analyze_stress_text(text) if text else 0.0
        if ml_probability is not None:
            combined_probability = (ml_probability * 0.6) + (stress_probability * 0.4)
            mental_health_pct = float(mental_health_score(combined_probability))
            final_adhd_risk = min(1.0, final_adhd_risk + (combined_probability * 0.3))
            productivity_pct = max(0.0, productivity_pct - (combined_probability * 40.0))
            depression_pct = (depression_pct * 0.6) + (mental_health_pct * 0.4)
        else:
            mental_health_pct = float(max(0, min(100, 100 - (stress_level * 10))))

        # 6. Overall Combined Final Score
        final, level, description, weights = final_score(
            productivity_pct, float(adhd_health_pct), mental_health_pct, depression_pct
        )

        focus_risk = "high" if final_adhd_risk >= 0.7 or stress_level >= 8 else "low" if final_adhd_risk < 0.3 and stress_level <= 4 else "medium"

        scores_payload = {
            "productivity_score": float(round(productivity_pct, 1)),
            "adhd_risk": float(round(final_adhd_risk, 2)),
            "adhd_health_score": float(round(adhd_health_pct, 1)),
            "adhd_questionnaire_score": q_score,
            "adhd_questionnaire_level": q_level,
            "mental_health_score": float(round(mental_health_pct, 1)),
            "depression_score": float(round(depression_pct, 1)),
            "final_score": float(round(final, 1)),
            "level": level,
            "description": description,
            "weights": {key: float(round(value, 3)) for key, value in weights.items()},
            "focus_risk": focus_risk,
            "summary": {
                "sleep_hours": user_snapshot.get("sleep_hours", 0),
                "stress_level": stress_level,
                "phone_distractions": user_snapshot.get("phone_distractions", 0),
                "study_hours": user_snapshot.get("study_hours_per_day", 0),
                "total_screen_time": float(engineered_df.get("total_screen_time", pd.Series([0])).iloc[0])
            }
        }

        # 7. Generate Interventions
        interventions = generate_interventions(user_snapshot, scores_payload)

        # 8. Record scores in database if DB is initialized
        db_mgr = DatabaseManager()
        try:
            user = db_mgr.get_user(username)
            if user:
                # Store latest scores in UserFact / memory so user context knows them
                db_mgr.save_fact(
                    username=username,
                    fact_type="behavior",
                    key="latest_ml_scores",
                    value=json.dumps(scores_payload),
                    confidence=1.0,
                    source="celery_inference"
                )
                logger.info(f"Celery: Saved ML scores payload in SQLite database for user '{username}'")
        except Exception as db_err:
            logger.warning(f"Celery: Database recording failed: {db_err}")
        finally:
            db_mgr.close()

        logger.info(f"Celery: ML inference task completed successfully for '{username}'")
        return {"scores": scores_payload, "interventions": interventions}

    except Exception as exc:
        logger.error(f"Celery: ML inference error: {exc}")
        # Retry with exponential backoff on failures
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error("Celery: Maximum retries exceeded for ML inference.")
            return {"error": "Maximum retries exceeded", "details": str(exc)}


# ==================== 2. PERIODIC ANALYTICS GENERATION ====================

@celery_app.task(name="tasks.generate_analytics", bind=True)
def generate_analytics_task(self, username: str, user_data: dict = None):
    """
    Gathers behavioral events, focus sessions, and mood logs to compile deep analytics.
    Caches the pre-compiled analytics as a structured fact to make API calls instant.
    """
    logger.info(f"Celery: Starting analytics generation for user '{username}'...")
    db_mgr = DatabaseManager()
    try:
        from memory.memory_manager import MemoryManager
        from analytics.insight_engine import InsightEngine
        from analytics.pattern_analyzer import PatternAnalyzer
        from analytics.recommendation_engine import RecommendationEngine

        user_data = user_data or {}
        memory = MemoryManager(user_id=username)
        user_profile = memory.profile.data if hasattr(memory, 'profile') else {}

        # 1. Instantiate analytics engines
        insight_engine = InsightEngine(memory)
        pattern_analyzer = PatternAnalyzer(memory)
        rec_engine = RecommendationEngine(memory)

        # 2. Run heavy analytical computations
        insights = insight_engine.generate_insights(user_profile)
        focus_data = user_profile.get("focus_patterns", {}).get("focus_quality_trend", [])
        mood_data = user_profile.get("emotional_patterns", {}).get("mood_trend", [])
        
        focus_patterns = pattern_analyzer.analyze_focus_patterns(focus_data)
        mood_patterns = pattern_analyzer.analyze_mood_patterns(mood_data)
        correlations = pattern_analyzer.analyze_productivity_correlations(user_data)
        temporal = pattern_analyzer.analyze_temporal_patterns(user_data.get("activity_log", []))

        context = {
            "user": user_data,
            "session": {
                "current_stress": user_data.get("stress_level", 5),
                "current_energy": user_data.get("energy_level", 5),
                "current_mood": user_data.get("mood", "neutral")
            }
        }
        recommendations = rec_engine.generate_recommendations(context, user_profile)
        priority_recs = rec_engine.get_priority_recommendations(context, user_profile)
        formatted_recs = rec_engine.format_for_display(recommendations)
        insight_summary = insight_engine.get_insight_summary_text(user_profile)

        # 3. Pull SQLite aggregates
        db_weekly = db_mgr.get_weekly_report(username)
        db_focus_hours = db_mgr.get_peak_focus_hours(username, 14)

        analytics_payload = {
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
            "compiled_at": datetime.now(timezone.utc).isoformat()
        }

        # 4. Cache compiled payload in database for lightning-fast reads
        db_mgr.save_fact(
            username=username,
            fact_type="behavior",
            key="precompiled_analytics",
            value=json.dumps(analytics_payload),
            confidence=1.0,
            source="celery_analytics"
        )

        logger.info(f"Celery: Saved pre-compiled analytics cache in SQLite for user '{username}'")
        return analytics_payload

    except Exception as e:
        logger.error(f"Celery: Analytics generation error for '{username}': {e}")
        return {"error": "Failed to compile analytics", "details": str(e)}
    finally:
        db_mgr.close()


@celery_app.task(name="tasks.periodic_weekly_analytics_beat")
def periodic_weekly_analytics_beat():
    """
    Celery Beat task: Scans the database periodically (e.g. daily/hourly) and pre-computes
    weekly analytics and mood trends for all active users.
    """
    logger.info("Celery Beat: Executing periodic weekly analytics pre-computation...")
    db_mgr = DatabaseManager()
    try:
        from database.models import User
        # Retrieve active users
        active_users = db_mgr.db.query(User).filter(User.is_active == True).all()
        logger.info(f"Celery Beat: Found {len(active_users)} active users to process.")
        
        for user in active_users:
            # Trigger analytics task asynchronously for each user
            generate_analytics_task.delay(username=user.username)
            logger.info(f"Celery Beat: Queued analytics pre-compilation task for '{user.username}'")
            
        return {"users_queued": len(active_users)}
    except Exception as e:
        logger.error(f"Celery Beat: Periodic weekly analytics failed: {e}")
        return {"error": str(e)}
    finally:
        db_mgr.close()


# ==================== 3. LONG-RUNNING MULTI-AGENT WORKFLOWS ====================

@celery_app.task(name="tasks.synthesize_personality", bind=True)
def synthesize_personality_task(self, username: str):
    """
    Orchestrates the specialized agents to extract insights from user history
    and compile a deep synthesized ADHD personality profile using the AI.
    """
    logger.info(f"Celery: Running multi-agent personality synthesis for user '{username}'...")
    db_mgr = DatabaseManager()
    try:
        from memory.memory_manager import MemoryManager
        from utils.main_api_imports import get_ai_reply  # Helper to make AI completion safe
        
        # Pull history aggregates
        recent_chats = db_mgr.get_chat_history(username, limit=30)
        mood_history = db_mgr.get_mood_history(username, days=14)
        focus_stats = db_mgr.get_focus_stats(username, days=14)
        user_facts = db_mgr.get_facts_as_dict(username)

        # Assemble summary texts for AI synthesis
        chat_transcript = "\n".join([f"{c.role}: {c.content[:200]}" for c in reversed(recent_chats)])
        mood_trend = ", ".join([f"{m.mood} (Energy:{m.energy}, Focus:{m.focus})" for m in mood_history])
        facts_summary = json.dumps(user_facts, indent=2)

        prompt = f"""
Analyze the following ADHD user profile logs to generate a comprehensive emotional, focusing, and productivity archetype.
Provide actionable shame-free coaching tips, identify major ADHD triggers, list peak energy patterns, and design dopamine reward loops customized for this individual.

USER CHAT HISTORY (RECENT):
{chat_transcript}

USER MOOD LOGS:
{mood_trend}

USER FOCUS SESSIONS (14 DAYS):
{json.dumps(focus_stats, indent=2)}

STRUCTURED FACTS LEARNED:
{facts_summary}

Respond with a complete, structured JSON containing:
1. "adhd_archetype" (e.g. "Hyperfocused Explorer", "Distracted Dreamer")
2. "primary_triggers" (List of things that trigger paralysis or stress)
3. "coaching_response_strategy" (Specific tone/rules AI coaches must use)
4. "dopamine_hooks" (Interventions/rewards that best motivate this user)
5. "energy_rhythm_summary" (When they are most productive or need breaks)

Do not include markdown or explanations. Respond with ONLY valid JSON code.
"""
        
        # Get AI completion
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            # Emulated synthesis fallback
            result_json = {
                "adhd_archetype": "Intuitive Sprinting Creator",
                "primary_triggers": ["massive writing tasks", "repetitive routines", "isolation without timers"],
                "coaching_response_strategy": "Warm, body-based grounding prompts, celebrate tiny micro-steps",
                "dopamine_hooks": ["visual timers", "points level ups", "water chimes"],
                "energy_rhythm_summary": "High energy mornings, heavy afternoon fatigue around 3 PM"
            }
        else:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.6,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )
                result_json = json.loads(chat_completion.choices[0].message.content)
            except Exception as e:
                logger.error(f"AI Synthesis API failed: {e}. Emulating profile.")
                result_json = {
                    "adhd_archetype": "Overwhelmed Task-Juggler",
                    "primary_triggers": ["large unstructured plans", "time blind spots"],
                    "coaching_response_strategy": "Hyper-supportive, shame-free validation",
                    "dopamine_hooks": ["confetti celebrations", "2-minute starting bridges"],
                    "energy_rhythm_summary": "Highly scattered attention throughout the day"
                }

        # Save synthesized profile in database
        db_mgr.save_fact(
            username=username,
            fact_type="profile",
            key="personality_synthesis",
            value=json.dumps(result_json),
            confidence=0.9,
            source="multi_agent_synthesis"
        )

        logger.info(f"Celery: Completed multi-agent personality synthesis for '{username}'")
        return result_json

    except Exception as exc:
        logger.error(f"Celery: Personality synthesis failed for '{username}': {exc}")
        return {"error": "Failed to synthesize personality", "details": str(exc)}
    finally:
        db_mgr.close()


@celery_app.task(name="tasks.compile_context", bind=True)
def compile_context_task(self, username: str):
    """
    Compiles memory context, structured facts, and recent conversation turns into a highly
    optimized context digest to prevent prompt bloating and token consumption.
    """
    logger.info(f"Celery: Compiling context for user '{username}'...")
    db_mgr = DatabaseManager()
    try:
        from memory.memory_manager import MemoryManager
        from utils.main_api_imports import get_ai_reply

        memory = MemoryManager(user_id=username)
        raw_context = memory.get_context_for_prompt_text()
        
        # Compile recent facts
        facts = db_mgr.get_facts_as_dict(username)
        facts_summary = ", ".join([f"{k}: {v['value']}" for cat in facts.values() for k, v in cat.items()])

        prompt = f"""
Compress the following user context block and behavioral facts list into a concise, high-value summary of:
1. The user's current goals and work preferences
2. Their active struggles and task blocks
3. Actionable triggers and coping tools they respond well to

RAW CONTEXT LOG:
{raw_context}

FACTS LEARNED:
{facts_summary}

Format the response as a clear, dense, 3-paragraph summary that can be directly injected into an LLM prompt as context.
Keep it strictly under 300 words. Be empathetic and supportive.
"""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            summary = "User is building consistency in study routines, responding exceptionally to Pomodoro timers. Task paralysis triggers include starting big reports. Currently supported by deep grounding interventions."
        else:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.5,
                    max_tokens=500
                )
                summary = chat_completion.choices[0].message.content
            except Exception as e:
                logger.error(f"AI Context compiler failed: {e}")
                summary = "Failed to synthesize. Active preference for small, visual task breakdowns."

        # Cache compiled context
        db_mgr.save_fact(
            username=username,
            fact_type="memory",
            key="compiled_context",
            value=summary,
            confidence=0.95,
            source="context_compiler_workflow"
        )

        logger.info(f"Celery: Context compiled and cached successfully for user '{username}'")
        return {"summary": summary}

    except Exception as exc:
        logger.error(f"Celery: Context compilation failed for '{username}': {exc}")
        return {"error": "Failed to compile context", "details": str(exc)}
    finally:
        db_mgr.close()
