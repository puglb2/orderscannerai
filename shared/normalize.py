import re

def normalize_medical_facts(text: str) -> dict:
    text_lower = text.lower()

    conditions = []
    medications = []

    # Very simple starters (we can expand later)
    if "diabetes" in text_lower:
        conditions.append("Diabetes Mellitus")

    if "hypertension" in text_lower or "htn" in text_lower:
        conditions.append("Hypertension")

    if "asthma" in text_lower:
        conditions.append("Asthma")

    if "metformin" in text_lower:
        medications.append("Metformin")

    if "insulin" in text_lower:
        medications.append("Insulin")

    return {
        "conditions": list(set(conditions)),
        "medications": list(set(medications))
    }
