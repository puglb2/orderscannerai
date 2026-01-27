def compute_insurability_score(facts: dict) -> dict:
    score = 0
    reasons = []

    for condition in facts["conditions"]:
        if condition == "Diabetes Mellitus":
            score += 2
            reasons.append("Diabetes (+2)")

        if condition == "Hypertension":
            score += 1
            reasons.append("Hypertension (+1)")

        if condition == "Asthma":
            score += 1
            reasons.append("Asthma (+1)")

    score = min(score, 10)

    return {
        "score": score,
        "reasons": reasons
    }
