def calculate_score(data):

    score = 0
    breakdown = []

    try:

        conditions = data.get("conditions", {})

        if conditions.get("diabetes_type") == "type1":
            score += 2.5
            breakdown.append("Type 1 diabetes")

        if data.get("has_stroke"):
            score += 2.0
            breakdown.append("Stroke")

        if data.get("has_neuropathy"):
            score += 0.5
            breakdown.append("Neuropathy")

        if data.get("has_retinopathy"):
            score += 1.2
            breakdown.append("Retinopathy")

        medications = data.get("medications", [])

        if isinstance(medications, list) and len(medications) >= 10:
            score += 0.5
            breakdown.append("Polypharmacy")

    except Exception:
        pass

    score = min(score, 10)

    return {
        "score": score,
        "breakdown": breakdown
    }
