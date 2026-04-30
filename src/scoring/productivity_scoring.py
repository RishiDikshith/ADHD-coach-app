def productivity_score(prediction):
    """
    prediction from productivity model
    Clamp score between 0–100
    """

    score = max(0, min(100, prediction))
    return score


# Alias for backward compatibility
calculate_productivity_score = productivity_score