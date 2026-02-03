def format_underwriting_text(facts, score_result):
    lines = []

    score = score_result.get("score", 0)
    breakdown = score_result.get("breakdown", [])

    # -------------------------
    # Header
    # -------------------------
    lines.append("UNDERWRITING SUMMARY")
    lines.append("--------------------")
    lines.append(f"Overall insurability risk score: {score} / 10.")
    lines.append("")

    # -------------------------
    # Clinical interpretation (non-AI, rule-based)
    # -------------------------
    if score <= 2:
        lines.append("This record reflects low underwriting risk.")
    elif score <= 4:
        lines.append("This record reflects low-to-moderate underwriting risk.")
    elif score <= 6:
        lines.append("This record reflects moderate underwriting risk.")
    elif score <= 8:
        lines.append("This record reflects elevated underwriting risk.")
    else:
        lines.append("This record reflects very high underwriting risk and may be uninsurable.")

    lines.append("")

    # -------------------------
    # Conditions summary
    # -------------------------
    conditions = facts.get("conditions", {})
    diabetes_type = conditions.get("diabetes_type")

    if diabetes_type in ("type1", "type2"):
        lines.append(f"- {diabetes_type.replace('type', 'Type ')} diabetes identified.")
    if conditions.get("active_cancer"):
        lines.append("- Active cancer is present.")
    if conditions.get("asthma"):
        lines.append("- History of asthma.")
    if conditions.get("arthritis"):
        lines.append("- History of arthritis.")

    # -------------------------
    # Vascular history
    # -------------------------
    macro = facts.get("macrovascular", {})
    if macro.get("stroke"):
        lines.append("- Prior cerebrovascular accident (stroke) documented.")
    elif macro.get("tia"):
        lines.append("- Prior transient ischemic attack documented.")

    if macro.get("cad_mi"):
        lines.append("- History of coronary artery disease or myocardial infarction.")
    if macro.get("pvd"):
        lines.append("- Peripheral vascular disease documented.")

    # -------------------------
    # Diabetes control
    # -------------------------
    diab = facts.get("diabetes_control", {})
    if isinstance(diab.get("a1c"), (int, float)):
        lines.append(f"- Most recent A1c reported at {diab['a1c']}.")
    if diab.get("insulin_pump_or_cgm"):
        lines.append("- Uses insulin pump or continuous glucose monitoring.")
    if diab.get("dka_hospitalization"):
        lines.append("- History of diabetic ketoacidosis hospitalization.")

    # -------------------------
    # Complications
    # -------------------------
    micro = facts.get("microvascular", {})
    if micro.get("neuropathy"):
        lines.append("- Diabetic neuropathy present.")
    if micro.get("retinopathy_stage") in ("non_proliferative", "proliferative"):
        stage = micro["retinopathy_stage"].replace("_", " ")
        lines.append(f"- Diabetic retinopathy ({stage}).")
    if isinstance(micro.get("ckd_stage"), (int, float)):
        lines.append(f"- Chronic kidney disease stage {micro['ckd_stage']}.")

    # -------------------------
    # Score drivers
    # -------------------------
    lines.append("")
    lines.append("Key underwriting drivers:")
    for item in breakdown:
        pts = item["points"]
        sign = "+" if pts > 0 else ""
        lines.append(f"- {item['item']} ({sign}{pts})")

    return "\n".join(lines)
