def depression_score(prediction):
    """
    prediction = 0 or 1 (depressed or not)
    """

    if prediction == 1:
        return 30
    else:
        return 80