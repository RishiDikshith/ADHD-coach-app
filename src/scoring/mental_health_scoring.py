def mental_health_score(prediction):
    """
    Convert mental health stress probability (0-1) to health score (0-100).
    
    Uses non-linear scaling for more realistic results:
    - 0.0 stress = 100 (Excellent)
    - 0.3 stress = 80 (Good)
    - 0.5 stress = 65 (Moderate)
    - 0.7 stress = 45 (Concerning)
    - 1.0 stress = 10 (Critical)
    
    Args:
        prediction: float - Stress probability (0-1)
        
    Returns:
        float - Health score (0-100, higher is better)
    """
    if prediction is None:
        return 50.0
    
    # Ensure prediction is in valid range
    prediction = max(0.0, min(1.0, float(prediction)))
    
    # Non-linear scaling for more realistic results
    # Uses exponential function to make small stress differences matter less
    # but critical stress levels stand out
    if prediction < 0.1:
        # 0-10% stress = 90-100 (Excellent to Great)
        score = 90 + (1 - prediction / 0.1) * 10
    elif prediction < 0.3:
        # 10-30% stress = 80-90 (Good)
        score = 80 + (1 - (prediction - 0.1) / 0.2) * 10
    elif prediction < 0.5:
        # 30-50% stress = 65-80 (Moderate)
        score = 65 + (1 - (prediction - 0.3) / 0.2) * 15
    elif prediction < 0.7:
        # 50-70% stress = 45-65 (Concerning)
        score = 45 + (1 - (prediction - 0.5) / 0.2) * 20
    else:
        # 70-100% stress = 10-45 (Concerning to Critical)
        score = 10 + (1 - (prediction - 0.7) / 0.3) * 35
    
    return float(max(10, min(100, round(score, 1))))


def get_stress_level_category(stress_probability):
    """
    Get stress level category (0-10 scale) from probability.
    
    Args:
        stress_probability: float - Stress probability (0-1)
        
    Returns:
        tuple - (level: 0-10, category: str, description: str)
    """
    stress_probability = max(0.0, min(1.0, float(stress_probability)))
    
    # Convert 0-1 probability to 0-10 scale
    stress_level = stress_probability * 10
    
    if stress_level < 1:
        category = "Minimal"
        description = "No detectable stress"
    elif stress_level < 2:
        category = "Very Low"
        description = "Minimal stress detected"
    elif stress_level < 3:
        category = "Low"
        description = "Slight stress, generally manageable"
    elif stress_level < 4:
        category = "Mild"
        description = "Mild stress present"
    elif stress_level < 5:
        category = "Moderate-Low"
        description = "Noticeable stress, manageable"
    elif stress_level < 6:
        category = "Moderate"
        description = "Moderate stress, some concern"
    elif stress_level < 7:
        category = "Moderate-High"
        description = "Higher stress, needs attention"
    elif stress_level < 8:
        category = "High"
        description = "Significant stress, intervention needed"
    elif stress_level < 9:
        category = "Very High"
        description = "Very high stress, urgent attention needed"
    else:
        category = "Critical"
        description = "Critical stress level, immediate support needed"
    
    return (round(stress_level, 1), category, description)


def analyze_stress_text(text):
    """
    Advanced stress detection with multi-level analysis.
    
    Args:
        text: str - User input text to analyze
        
    Returns:
        float - Stress score from 0-1 (0 = no stress, 1 = high stress)
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    text_lower = text.lower().strip()
    if len(text_lower) < 3:
        return 0.0
    
    # Level 1: Critical stress indicators (highest severity)
    critical_indicators = {
        "suicide": 0.95,
        "harm myself": 0.95,
        "panic attack": 0.85,
        "nervous breakdown": 0.85,
        "can't breathe": 0.8,
        "heart racing": 0.75,
        "severe anxiety": 0.8,
        "completely overwhelmed": 0.8,
    }
    
    # Level 2: High stress indicators
    high_stress_indicators = {
        "overwhelm": 0.6,
        "overwhelmed": 0.65,
        "panic": 0.65,
        "severe stress": 0.65,
        "burnout": 0.6,
        "burnt out": 0.6,
        "breaking down": 0.6,
        "can't cope": 0.65,
        "falling apart": 0.6,
        "tension": 0.6,
        "tense": 0.55,
    }
    
    # Level 3: Moderate stress indicators
    moderate_stress_indicators = {
        "stressed": 0.45,
        "stress": 0.4,
        "anxious": 0.45,
        "anxiety": 0.4,
        "worried": 0.35,
        "concerned": 0.25,
        "depressed": 0.5,
        "depression": 0.45,
        "exhausted": 0.4,
        "drained": 0.4,
        "worn out": 0.4,
        "tired all the time": 0.45,
        "can't focus": 0.45,
        "cant focus": 0.45,
        "can't concentrate": 0.45,
        "cant concentrate": 0.45,
        "difficulty focusing": 0.35,
        "distracted": 0.35,
        "no motivation": 0.4,
        "struggling": 0.35,
        "having trouble": 0.25,
        "hard time": 0.25,
        "not sleeping": 0.4,
        "insomnia": 0.45,
        "sleep issues": 0.35,
    }
    
    # Level 4: Mild stress indicators
    mild_stress_indicators = {
        "busy": 0.15,
        "busy schedule": 0.2,
        "a lot going on": 0.2,
        "hectic": 0.2,
        "tight deadline": 0.3,
        "pressure": 0.25,
        "worried about": 0.25,
        "concerned about": 0.2,
        "frustrated": 0.25,
        "annoyed": 0.15,
        "irritable": 0.2,
        "impatient": 0.1,
        "procrastinating": 0.25,
        "behind": 0.15,
        "stuck": 0.2,
        "difficult": 0.15,
        "challenging": 0.1,
    }
    
    # Positive/calming indicators (reduce stress score)
    positive_indicators = {
        "feeling better": -0.2,
        "much better": -0.25,
        "great": -0.15,
        "excellent": -0.15,
        "happy": -0.15,
        "calm": -0.2,
        "relaxed": -0.2,
        "manageable": -0.15,
        "under control": -0.2,
        "doing well": -0.15,
        "improving": -0.1,
        "better now": -0.2,
        "listen to music": -0.15,
        "listening to music": -0.15,
        "meditate": -0.15,
        "take a break": -0.1,
    }
    
    stress_score = 0.0
    indicator_count = 0
    
    # Check all stress indicator levels
    all_indicators = {
        **critical_indicators,
        **high_stress_indicators,
        **moderate_stress_indicators,
        **mild_stress_indicators,
        **positive_indicators,
    }
    
    # Find all matching indicators (cumulative approach)
    matched_indicators = []
    for indicator, value in all_indicators.items():
        if indicator in text_lower:
            matched_indicators.append((indicator, value))
            indicator_count += 1
    
    if not matched_indicators:
        return 0.0
    
    # Calculate stress score based on matched indicators
    if indicator_count == 1:
        # Single indicator: use its value directly
        stress_score = matched_indicators[0][1]
    else:
        # Multiple indicators: use weighted average with emphasis on higher severity
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for indicator, value in matched_indicators:
            # Weight by absolute value (higher stress = higher weight)
            weight = abs(value)
            weighted_sum += value * weight
            weight_sum += weight
        
        stress_score = weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    # Frequency boost: multiple mentions increase stress
    if indicator_count > 1:
        frequency_boost = min(0.15, (indicator_count - 1) * 0.05)
        stress_score = min(0.95, stress_score + frequency_boost)
    
    # Sentiment context: check for negations that might reduce stress
    negation_words = ["not", "no", "don't", "won't", "didn't", "can't", "couldn't"]
    text_words = text_lower.split()
    
    # If text is mostly questions, reduce stress (curiosity/seeking help is positive)
    question_ratio = text_lower.count("?") / max(1, len(text_words) / 10)
    if question_ratio > 0.3:
        stress_score *= 0.85  # 15% reduction for question-heavy text
    
    # Normalize to 0-1 scale with realistic bounds
    stress_score = max(0.0, min(1.0, stress_score))
    
    # Avoid extreme 0 or 1 unless explicitly critical
    if stress_score < 0.05:
        return 0.0
    elif stress_score > 0.9:
        # Only return near-1 if we have critical indicators
        has_critical = any(ind in text_lower for ind in critical_indicators.keys())
        if not has_critical:
            stress_score = min(0.75, stress_score)
    
    return stress_score