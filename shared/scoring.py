def calculate_score(structured):

    flags = structured.get("flags", {})
    meds = structured.get("medications", [])

    score = 0.0
    drivers = []

    # helper to keep everything consistent
    def add(points, label):
        nonlocal score
        score += points
        drivers.append(f"{label} [+{points}]")

    # -----------------------
    # CORE CONDITIONS
    # -----------------------

    if flags.get("cancer"):
        add(5.0, "Active cancer")

    if flags.get("diabetes"):
        add(2.5, "Diabetes")

    if flags.get("chf"):
        add(3.0, "Congestive heart failure")

    if flags.get("copd"):
        add(2.0, "COPD")

    if flags.get("heart_disease"):
        add(2.0, "Heart disease")

    if flags.get("stroke"):
        add(2.5, "Stroke history")

    if flags.get("chest_pain"):
        add(1.5, "Chest Pain")

    if flags.get("depression") or flags.get("anxiety"):
        add(1.5, "Mental health condition")

    # -----------------------
    # MEDICATION COMPLEXITY
    # -----------------------

    med_count = len(meds)

    if med_count > 0:
        med_score = round(med_count * 0.25, 2)
        add(med_score, f"Medication burden ({med_count} meds)")

    # -----------------------
    # NORMALIZE SCORE
    # -----------------------

    score = min(score, 10.0)

    explanation = "\n".join([f"- {d}" for d in drivers])

    return score, explanation
