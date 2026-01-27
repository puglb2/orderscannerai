def apply_rule_zero(facts: dict) -> dict:
    disqualifiers = []

    for condition in facts["conditions"]:
        if "stage iv" in condition.lower():
            disqualifiers.append(condition)

    return {
        "eligible": len(disqualifiers) == 0,
        "disqualifiers": disqualifiers
    }
