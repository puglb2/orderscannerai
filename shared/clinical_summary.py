def generate_clinical_summary(structured):

    patient = structured.get("patient", {})
    meds = structured.get("medications", [])
    providers = structured.get("providers", [])
    diagnoses = structured.get("diagnoses", [])
    icd = list(set(structured.get("icd_codes", [])))
    cpt = list(set(structured.get("cpt_codes", [])))

    # -----------------------
    # DEMOGRAPHICS
    # -----------------------
    header = f"""RECORD SUMMARY
--------------
Name: {patient.get("name","Kevin Smith")}
DOB: {patient.get("dob","Unknown")} | Age: {patient.get("age","Unknown")}
Gender: {patient.get("gender","Unknown")}
Race: {patient.get("race","Unknown")}
Height: {patient.get("height","Unknown")}
Weight: {patient.get("weight","Unknown")}
"""

    # -----------------------
    # BASIC SUMMARY (from structured only)
    # -----------------------
    summary = "This record reflects a patient with documented medical conditions and ongoing care."

    # -----------------------
    # DIAG + ICD TOGETHER
    # -----------------------
    diag_lines = []
    for i, d in enumerate(diagnoses):
        code = icd[i] if i < len(icd) else ""
        diag_lines.append(f"- {d} ({code})" if code else f"- {d}")

    diag_text = "\n".join(diag_lines) if diag_lines else "None"

    # -----------------------
    # MEDS
    # -----------------------
    med_lines = "\n".join([
        f"- {m.get('name')} ({m.get('status','unknown')})"
        for m in meds
    ]) if meds else "None"

    # -----------------------
    # PROVIDERS
    # -----------------------
    provider_lines = "\n".join([
        f"- {p.get('name','Unknown')} ({p.get('specialty','Unknown')}) {p.get('address','')}"
        for p in providers
    ]) if providers else "None"

    # -----------------------
    # CPT
    # -----------------------
    cpt_text = "\n".join(cpt) if cpt else "None"

    return f"""{header}

SUMMARY
-------
{summary}

DIAGNOSES (ICD)
---------------
{diag_text}

MEDICATIONS
-----------
{med_lines}

PROVIDERS
---------
{provider_lines}

CPT CODES
---------
{cpt_text}
"""
