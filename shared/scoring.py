def calculate_score(structured):

    flags = structured.get("flags", {})
    score = 0
    drivers = []

    if flags.get("diabetes"):
        score += 2
        drivers.append("Diabetes")

    if flags.get("cancer"):
        score += 5
        drivers.append("Cancer")

    if flags.get("chf"):
        score += 3
        drivers.append("Congestive Heart Failure")

    if flags.get("copd"):
        score += 2
        drivers.append("COPD")

    if flags.get("heart_disease"):
        score += 2
        drivers.append("Heart Disease")

    if flags.get("stroke"):
        score += 2
        drivers.append("Stroke")

    if flags.get("depression"):
        score += 2
        drivers.append("Depression")

    if flags.get("chest_pain"):
        score += 2
        drivers.append("Chest Pain")

    score = min(score, 10)

    explanation = "\n".join([f"• {d}" for d in drivers])

    return score, explanation
