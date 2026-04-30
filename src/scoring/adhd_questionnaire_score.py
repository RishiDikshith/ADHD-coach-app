def calculate_adhd_score(answers):
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