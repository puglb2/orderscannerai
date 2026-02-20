def calculate_score(data):

    score = 0.0
    drivers = []

    conditions = data.get("conditions", {})

    # Rule 1 — Base Conditions
    if conditions.get("diabetes_type") == "type1":
        score += 2.5
        drivers.append("Type 1 diabetes")

    if conditions.get("diabetes_type") == "type2":
        score += 2.0
        drivers.append("Type 2 diabetes")

    if conditions.get("active_cancer"):
        score += 5.0
        drivers.append("Active cancer")

    if conditions.get("asthma"):
        score += 0.5
        drivers.append("Asthma")

    if conditions.get("arthritis"):
        score += 0.5
        drivers.append("Arthritis")

    # Rule 4 — Macrovascular
    if data.get("has_stroke"):
        score += 2.0
        drivers.append("History of stroke")

    if data.get("has_tia"):
        score += 1.0
        drivers.append("History of TIA")

    # Rule 3 — Microvascular
    if data.get("has_neuropathy"):
        score += 0.5
        drivers.append("Neuropathy")

    if data.get("has_retinopathy"):
        score += 1.2
        drivers.append("Retinopathy")

    # Medications
    meds = data.get("medications", [])
    if isinstance(meds, list) and len(meds) >= 10:
        score += 0.5
        drivers.append(f"Polypharmacy ({len(meds)} medications)")

    # Cap score at 10
    score = min(round(score, 1), 10)

    return {
        "score": score,
        "drivers": drivers
    }
