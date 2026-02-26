def calculate_score(structured):

    flags = structured.get("flags", {})
    meds = structured.get("medications", [])

    score = 0.0
    drivers = []

    # -----------------------
    # CORE CONDITIONS
    # -----------------------

    if flags.get("cancer"):
        score += 5.0
        drivers.append("Active cancer")

    if flags.get("diabetes"):
        score += 2.5
        drivers.append("Diabetes")

    if flags.get("chf"):
        score += 3.0
        drivers.append("Congestive heart failure")

    if flags.get("copd"):
        score += 2.0
        drivers.append("COPD")

    if flags.get("heart_disease"):
        score += 2.0
        drivers.append("Heart disease")

    if flags.get("stroke"):
        score += 2.5
        drivers.append("Stroke history")

    if flags.get("depression") or flags.get("anxiety"):
        score += 1.5
        drivers.append("Mental health condition")

    # -----------------------
    # MEDICATION COMPLEXITY
    # -----------------------

    med_count = len(meds)

    if med_count >= 20:
        score += 1.0
        drivers.append("High medication burden (20+)")

    elif med_count >= 10:
        score += 0.5
        drivers.append("Moderate medication burden (10+)")

    # -----------------------
    # NORMALIZE SCORE
    # -----------------------

    score = min(score, 10.0)

    explanation = "\n".join([f"- {d}" for d in drivers])

    return score, explanation
