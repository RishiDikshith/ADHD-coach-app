def calculate_adhd_score(answers):
    """
    Calculate ADHD score from questionnaire answers.
    
    Args:
        answers: list of str - Answers like ["Never", "Often", "Very Often", ...]
        
    Returns:
        tuple: (total_score, level)
    """
    score_map = {
        "Never": 0,
        "Rarely": 1,
        "Sometimes": 2,
        "Often": 3,
        "Very Often": 4
    }

    total_score = 0

    for answer in answers:
        total_score += score_map.get(answer, 0)

    if total_score <= 16:
        level = "Low ADHD"
    elif total_score <= 24:
        level = "Moderate ADHD"
    else:
        level = "High ADHD"

    return total_score, level


def combined_adhd_score(questionnaire_score, ml_risk):

    # Normalize questionnaire (0–36 → 0–1)
    q_score = questionnaire_score / 36

    # 🔥 FIX: normalize ML risk safely
    ml_risk = max(0, min(1, ml_risk))

    # Combine
    final_risk = (0.6 * ml_risk) + (0.4 * q_score)

    # Convert to health score
    adhd_health_score = (1 - final_risk) * 100

    # Clamp again
    adhd_health_score = max(0, min(100, adhd_health_score))

    return adhd_health_score, final_risk