def compute_underwriting_score_v1(facts):
    breakdown = []

    def add(rule, item, points):
        if points != 0:
            breakdown.append({
                "rule": rule,
                "item": item,
                "points": points
            })
        return points

    # Safe access helpers
    conditions = facts.get("conditions", {}) or {}
    diab = facts.get("diabetes_control", {}) or {}
    micro = facts.get("microvascular", {}) or {}
    macro = facts.get("macrovascular", {}) or {}
    meds = facts.get("medications", {}) or {}
    stability = facts.get("stability", {}) or {}

    total = 0.0

    # ---------------- RULE 1 — BASE CONDITIONS ----------------
    dt = (conditions.get("diabetes_type") or "").lower()
    if dt == "type1":
        total += add("RULE 1", "Type 1 diabetes", 2.5)
    elif dt == "type2":
        total += add("RULE 1", "Type 2 diabetes", 2.0)

    if conditions.get("active_cancer") is True:
        total += add("RULE 1", "Active cancer", 5.0)

    if conditions.get("asthma") is True:
        total += add("RULE 1", "Asthma (controlled)", 0.5)

    if conditions.get("arthritis") is True:
        total += add("RULE 1", "Arthritis", 0.5)

    # ---------------- RULE 2 — GLYCEMIC MODIFIERS ----------------
    a1c = diab.get("a1c")
    if isinstance(a1c, (int, float)):
        if a1c > 8.5:
            total += add("RULE 2", "A1c > 8.5", 1.0)
        elif a1c >= 7.0:
            total += add("RULE 2", "A1c 7.0–8.5", 0.5)

    if diab.get("insulin_pump_or_cgm") is True:
        total += add("RULE 2", "Insulin pump / CGM", 0.3)

    if diab.get("recurrent_hypoglycemia") is True:
        total += add("RULE 2", "Recurrent hypoglycemia", 0.5)

    if diab.get("dka_hospitalization") is True:
        total += add("RULE 2", "DKA hospitalization", 1.5)

    # ---------------- RULE 3 — MICROVASCULAR (cap 3.0) ----------------
    micro_total = 0.0

    if micro.get("neuropathy") is True:
        micro_total += add("RULE 3", "Neuropathy", 0.5)

    ret = (micro.get("retinopathy_stage") or "").lower()
    if ret == "non_proliferative":
        micro_total += add("RULE 3", "Non-proliferative retinopathy", 0.7)
    elif ret == "proliferative":
        micro_total += add("RULE 3", "Proliferative retinopathy", 1.2)

    ckd = micro.get("ckd_stage")
    if isinstance(ckd, (int, float)):
        if ckd >= 3:
            micro_total += add("RULE 3", "CKD stage 3+", 1.5)
        elif ckd >= 1:
            micro_total += add("RULE 3", "CKD stage 1–2", 0.5)

    micro_total = min(micro_total, 3.0)
    total += micro_total

    # ---------------- RULE 4 — MACROVASCULAR ----------------
    if macro.get("stroke") is True:
        total += add("RULE 4", "Stroke (CVA)", 2.0)
    elif macro.get("tia") is True:
        total += add("RULE 4", "TIA", 1.0)

    if macro.get("cad_mi") is True:
        total += add("RULE 4", "CAD / MI", 2.0)

    if macro.get("pvd") is True:
        total += add("RULE 4", "Peripheral vascular disease", 1.0)

    # ---------------- RULE 5 — MEDICATION SEVERITY ----------------
    if meds.get("dual_antiplatelet") is True:
        total += add("RULE 5", "Dual antiplatelet therapy", 0.5)

    if meds.get("midodrine") is True:
        total += add("RULE 5", "Midodrine", 0.5)

    if isinstance(meds.get("chronic_med_count"), (int, float)) and meds["chronic_med_count"] >= 10:
        total += add("RULE 5", "≥10 chronic medications", 0.5)

    if meds.get("has_glucagon") is True:
        total += add("RULE 5", "Glucagon", 0.3)

    # ---------------- RULE 6 — STABILITY ----------------
    if isinstance(stability.get("last_hospitalization_months_ago"), (int, float)):
        if stability["last_hospitalization_months_ago"] >= 36:
            total += add("RULE 6", "No hospitalizations ≥3 years", -0.5)
        elif stability["last_hospitalization_months_ago"] < 12:
            total += add("RULE 6", "Recent hospitalization", 0.5)

    if isinstance(stability.get("last_dka_years_ago"), (int, float)) and stability["last_dka_years_ago"] >= 5:
        total += add("RULE 6", "No DKA ≥5 years", -0.5)

    if stability.get("labs_worsening") is True:
        total += add("RULE 6", "Worsening labs", 0.5)

    total = max(0.0, min(10.0, round(total, 2)))

    return {
        "score": total,
        "breakdown": breakdown
    }
