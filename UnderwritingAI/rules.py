def evidence_threshold(condition):
    """
    Rule 0:
    condition = {
        "mentions": int,
        "source": ["HPI", "Assessment", "Labs", "Meds"]
    }
    """
    if condition["mentions"] >= 2:
        return 1.0

    if "Labs" in condition["source"] or "Imaging" in condition["source"]:
        return 1.0

    if "HPI" in condition["source"]:
        return 0.5

    return 0.0
