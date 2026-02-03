from typing import Dict, Any, List, Tuple


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _add(breakdown: List[Dict[str, Any]], rule: str, label: str, points: float) -> float:
    if abs(points) > 1e-9:
        breakdown.append({"rule": rule, "item": label, "points": points})
    return points


def compute_underwriting_score_v1(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes 0-10 risk score using:
    RULE 1: Base condition
    RULE 2: Glycemic modifiers
    RULE 3: Microvascular (cap 3.0)
    RULE 4: Macrovascular (no cap)
    RULE 5: Medication severity
    RULE 6: Stability adjustments

    Output includes totals + breakdown for explainability.
    """

    breakdown: List[Dict[str, Any]] = []

    conditions = facts.get("conditions", {})
    diab = facts.get("diabetes_control", {})
    micro = facts.get("microvascular", {})
    macro = facts.get("macrovascular", {})
    meds = facts.get("medications", {})
    stability = facts.get("stability", {})

    # ---------------------------
    # RULE 1 — BASE CONDITION SCORE
    # ---------------------------
    base = 0.0
    diabetes_type = (conditions.get("diabetes_type") or "unknown").lower()

    # Cancer (active)
    if conditions.get("active_cancer") is True:
        base += _add(breakdown, "RULE 1", "Cancer (active)", 5.0)

    # Diabetes base (presence only)
    if diabetes_type == "type1":
        base += _add(breakdown, "RULE 1", "Type 1 diabetes (no complications)", 2.5)
    elif diabetes_type == "type2":
        base += _add(breakdown, "RULE 1", "Type 2 diabetes (no complications)", 2.0)
    # none/unknown => no base points for diabetes unless you choose to default later

    # Asthma (controlled)
    if conditions.get("asthma") is True:
        base += _add(breakdown, "RULE 1", "Asthma (controlled)", 0.5)

    # Arthritis
    if conditions.get("arthritis") is True:
        base += _add(breakdown, "RULE 1", "Arthritis", 0.5)

    # If truly no chronic disease flags and diabetes_type==none and not active cancer
    # (Optional: leave at 0.0 naturally)

    # ---------------------------
    # RULE 2 — GLYCEMIC CONTROL MODIFIERS (Diabetes)
    # ---------------------------
    glycemic = 0.0
    has_diabetes = diabetes_type in ("type1", "type2")

    if has_diabetes:
        a1c = diab.get("a1c", None)
        # A1c tiers
        if isinstance(a1c, (int, float)):
            if a1c < 7.0:
                glycemic += _add(breakdown, "RULE 2", "A1c < 7.0", 0.0)
            elif 7.0 <= a1c <= 8.5:
                glycemic += _add(breakdown, "RULE 2", "A1c 7.0–8.5", 0.5)
            elif a1c > 8.5:
                glycemic += _add(breakdown, "RULE 2", "A1c > 8.5", 1.0)
        else:
            # If A1c missing, we do NOT guess a tier automatically here.
            # (If you want your earlier default behavior, change this to +0.5.)
            pass

        # Pump/CGM
        if diab.get("insulin_pump_or_cgm") is True:
            glycemic += _add(breakdown, "RULE 2", "Insulin pump / CGM", 0.3)

        # Recurrent hypoglycemia
        if diab.get("recurrent_hypoglycemia") is True:
            glycemic += _add(breakdown, "RULE 2", "Recurrent hypoglycemia", 0.5)

        # DKA hospitalization
        if diab.get("dka_hospitalization") is True:
            glycemic += _add(breakdown, "RULE 2", "DKA (≥1 hospitalization)", 1.5)

    # ---------------------------
    # RULE 3 — MICROVASCULAR COMPLICATIONS (cap at 3.0)
    # ---------------------------
    micro_points = 0.0

    if micro.get("neuropathy") is True:
        micro_points += _add(breakdown, "RULE 3", "Neuropathy", 0.5)

    ret_stage = (micro.get("retinopathy_stage") or "none").lower()
    if ret_stage == "non_proliferative":
        micro_points += _add(breakdown, "RULE 3", "Retinopathy (non-proliferative)", 0.7)
    elif ret_stage == "proliferative":
        micro_points += _add(breakdown, "RULE 3", "Proliferative retinopathy / injections", 1.2)
    # unknown/none => 0

    ckd_stage = micro.get("ckd_stage", None)
    if isinstance(ckd_stage, (int, float)):
        if 1 <= ckd_stage <= 2:
            micro_points += _add(breakdown, "RULE 3", "CKD Stage 1–2", 0.5)
        elif ckd_stage >= 3:
            micro_points += _add(breakdown, "RULE 3", "CKD Stage 3+", 1.5)

    # Apply cap
    if micro_points > 3.0:
        breakdown.append({"rule": "RULE 3", "item": "Microvascular cap applied", "points": 0.0, "note": "capped at 3.0"})
    micro_points = min(micro_points, 3.0)

    # ---------------------------
    # RULE 4 — MACROVASCULAR EVENTS (no cap)
    # ---------------------------
    macro_points = 0.0
    # Stroke > TIA (avoid double count if both true)
    stroke = macro.get("stroke") is True
    tia = macro.get("tia") is True

    if stroke:
        macro_points += _add(breakdown, "RULE 4", "Stroke (CVA)", 2.0)
    elif tia:
        macro_points += _add(breakdown, "RULE 4", "TIA", 1.0)

    if macro.get("cad_mi") is True:
        macro_points += _add(breakdown, "RULE 4", "CAD / MI", 2.0)

    if macro.get("pvd") is True:
        macro_points += _add(breakdown, "RULE 4", "Peripheral vascular disease", 1.0)

    # ---------------------------
    # RULE 5 — MEDICATION SEVERITY MODIFIERS
    # ---------------------------
    med_points = 0.0
    if meds.get("dual_antiplatelet") is True:
        med_points += _add(breakdown, "RULE 5", "Dual antiplatelet therapy", 0.5)

    if meds.get("midodrine") is True:
        med_points += _add(breakdown, "RULE 5", "Midodrine (chronic hypotension)", 0.5)

    med_count = meds.get("chronic_med_count", None)
    if isinstance(med_count, (int, float)) and med_count >= 10:
        med_points += _add(breakdown, "RULE 5", "≥10 chronic medications", 0.5)

    if meds.get("has_glucagon") is True:
        med_points += _add(breakdown, "RULE 5", "Rescue meds (glucagon)", 0.3)

    # ---------------------------
    # RULE 6 — STABILITY & TRAJECTORY ADJUSTMENT
    # ---------------------------
    stability_points = 0.0

    # No hospitalizations >= 3 years => months >= 36
    last_hosp_mo = stability.get("last_hospitalization_months_ago", None)
    if isinstance(last_hosp_mo, (int, float)):
        if last_hosp_mo >= 36:
            stability_points += _add(breakdown, "RULE 6", "No hospitalizations ≥3 years", -0.5)
        elif last_hosp_mo < 12:
            stability_points += _add(breakdown, "RULE 6", "Recent hospitalization (<12 mo)", 0.5)

    # No DKA >= 5 years
    last_dka_yr = stability.get("last_dka_years_ago", None)
    if isinstance(last_dka_yr, (int, float)) and last_dka_yr >= 5:
        stability_points += _add(breakdown, "RULE 6", "No DKA ≥5 years", -0.5)

    # Worsening labs trend
    if stability.get("labs_worsening") is True:
        stability_points += _add(breakdown, "RULE 6", "Worsening labs trend", 0.5)

    # ---------------------------
    # TOTAL + CLAMP
    # ---------------------------
    raw_total = base + glycemic + micro_points + macro_points + med_points + stability_points
    total = clamp(raw_total, 0.0, 10.0)

    return {
        "score": round(total, 2),
        "raw_total": round(raw_total, 2),
        "components": {
            "base": round(base, 2),
            "glycemic": round(glycemic, 2),
            "microvascular": round(micro_points, 2),
            "macrovascular": round(macro_points, 2),
            "medication": round(med_points, 2),
            "stability": round(stability_points, 2),
        },
        "breakdown": breakdown
    }
