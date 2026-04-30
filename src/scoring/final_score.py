def final_score(productivity, adhd, mental_health, depression):
    """
    Calculate comprehensive ADHD productivity score with dynamic weighting.
    Adjusts weights based on individual risk factors.
    """

    # Base weights
    base_weights = {
        "productivity": 0.35,
        "adhd": 0.25,
        "mental_health": 0.20,
        "depression": 0.20
    }

    # Dynamic weighting based on risk levels
    if adhd < 40:  # High ADHD risk
        base_weights["adhd"] += 0.1
        base_weights["productivity"] -= 0.05
        base_weights["mental_health"] -= 0.05

    if mental_health < 50:  # Poor mental health
        base_weights["mental_health"] += 0.1
        base_weights["depression"] += 0.05
        base_weights["productivity"] -= 0.1
        base_weights["adhd"] -= 0.05

    if depression < 50:  # Depression risk
        base_weights["depression"] += 0.1
        base_weights["mental_health"] += 0.05
        base_weights["productivity"] -= 0.1
        base_weights["adhd"] -= 0.05

    # Normalize weights to sum to 1
    total_weight = sum(base_weights.values())
    weights = {k: v/total_weight for k, v in base_weights.items()}

    # Calculate weighted score
    score = (
        weights["productivity"] * productivity +
        weights["adhd"] * adhd +
        weights["mental_health"] * mental_health +
        weights["depression"] * depression
    )

    # Clamp score
    score = max(0, min(100, score))

    # Determine level with more granularity
    if score >= 85:
        level = "Excellent"
        description = "Outstanding ADHD management and productivity"
    elif score >= 75:
        level = "Good"
        description = "Good overall performance with room for improvement"
    elif score >= 65:
        level = "Moderate"
        description = "Moderate performance - focus on key areas"
    elif score >= 50:
        level = "Concerning"
        description = "Some areas need attention"
    else:
        level = "Critical"
        description = "Immediate intervention recommended"

    return score, level, description, weights


# Aliases for backward compatibility
calculate_final_score = final_score


def get_level_from_score(score):
    """
    Get level classification from a numeric score.
    
    Args:
        score: float between 0-100
        
    Returns:
        str: level classification
    """
    if score >= 85:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 65:
        return "Moderate"
    elif score >= 50:
        return "Concerning"
    else:
        return "Critical"