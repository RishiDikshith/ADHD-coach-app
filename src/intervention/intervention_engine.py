def _score_value(scores, *keys, default=0):
    for key in keys:
        value = scores.get(key)
        if value is not None:
            return value
    return default


def generate_interventions(data, scores):
    """
    Generate personalized, prioritized interventions based on user data and scores.
    Uses rule-based logic with prioritization.
    """
    data = data or {}
    scores = scores or {}
    interventions = []
    total_screen_time = data.get("total_screen_time")
    if total_screen_time is None:
        total_screen_time = (
            data.get("phone_usage_hours", 0)
            + data.get("social_media_hours", 0)
            + data.get("youtube_hours", 0)
            + data.get("gaming_hours", 0)
        )

    adhd_risk = _score_value(scores, "adhd_risk", "final_adhd_risk", default=0)
    productivity = _score_value(scores, "productivity", "productivity_score", default=100)
    mental_health = _score_value(scores, "mental_health", "mental_health_score", default=100)

    # High Priority Interventions
    if data.get("sleep_hours", 0) < 6:
        interventions.append({
            "priority": "high",
            "category": "sleep",
            "title": "Improve Sleep Quality",
            "description": "Aim for 7-9 hours of sleep. Establish a consistent bedtime routine.",
            "action": "Set a fixed bedtime and avoid screens 1 hour before sleep."
        })

    if data.get("stress_level", 0) > 8:
        interventions.append({
            "priority": "high",
            "category": "stress",
            "title": "Manage High Stress",
            "description": "Your stress levels are elevated. Implement immediate stress reduction techniques.",
            "action": "Try 5-minute breathing exercises: inhale for 4 counts, hold for 4, exhale for 4."
        })

    if total_screen_time > 8:
        interventions.append({
            "priority": "high",
            "category": "digital",
            "title": "Reduce Screen Time",
            "description": "Excessive screen time can impact focus and sleep quality.",
            "action": "Use app blockers during study hours and set screen time limits."
        })

    if data.get("phone_distractions", 0) > 2:
        interventions.append({
            "priority": "high",
            "category": "distraction",
            "title": "Reduce Phone Interruptions",
            "description": "Frequent phone breaks can derail focus, especially for ADHD brains.",
            "action": "Turn on Do Not Disturb and keep your phone out of sight for the next focus session."
        })

    # Medium Priority Interventions
    if adhd_risk > 0.7:
        interventions.append({
            "priority": "medium",
            "category": "focus",
            "title": "ADHD Focus Sprint",
            "description": "When concentration is hard, a tiny timer helps you start without pressure.",
            "action": "Try a 10-minute sprint with one clear task, then take a quick 2-minute reset."
        })

    if data.get("exercise_minutes", 0) < 30:
        interventions.append({
            "priority": "medium",
            "category": "health",
            "title": "Increase Physical Activity",
            "description": "Regular exercise improves focus and reduces stress.",
            "action": "Aim for 30 minutes of activity daily - walking, gym, or sports."
        })

    if data.get("breaks_per_day", 0) < 3:
        interventions.append({
            "priority": "medium",
            "category": "breaks",
            "title": "Implement Regular Breaks",
            "description": "Proper breaks prevent burnout and improve productivity.",
            "action": "Take short 5-minute breaks every hour during study sessions."
        })

    if data.get("pause_count", 0) > 3:
        interventions.append({
            "priority": "medium",
            "category": "attention",
            "title": "Reduce Task Switching",
            "description": "Frequent pauses often mean your session is too long or unfocused.",
            "action": "Shorten the next task to 10 minutes and keep the next action extremely specific."
        })

    # Low Priority Interventions
    if productivity < 40:
        interventions.append({
            "priority": "low",
            "category": "productivity",
            "title": "Build Study Routine",
            "description": "Create a consistent study schedule for better productivity.",
            "action": "Plan your day: set specific times for study, breaks, and leisure."
        })

    if mental_health < 60:
        interventions.append({
            "priority": "low",
            "category": "mental_health",
            "title": "Mental Health Support",
            "description": "Consider additional support for mental well-being.",
            "action": "Talk to friends/family or consider professional counseling if needed."
        })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    interventions.sort(key=lambda x: priority_order[x["priority"]])

    return interventions[:5]  # Return top 5 interventions
