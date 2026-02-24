def generate_clinical_summary(structured):

    patient = structured.get("patient", {})
    meds = structured.get("medications", [])
    providers = structured.get("providers", [])
    diagnoses = structured.get("diagnoses", [])
    icd = list(set(structured.get("icd_codes", [])))
    cpt = list(set(structured.get("cpt_codes", [])))

    med_lines = "\n".join([
        f"- {m['name']} ({m.get('status','unknown')})"
        for m in meds
    ]) if meds else "None"

    provider_lines = "\n".join([
        f"- {p.get('name','Unknown')} ({p.get('specialty','Unknown')}) {p.get('address','')}"
        for p in providers
    ]) if providers else "None"

    dx_lines = "\n".join([f"- {d}" for d in diagnoses]) if diagnoses else "None"
    icd_lines = "\n".join([f"- {c}" for c in icd]) if icd else "None"
    cpt_lines = "\n".join([f"- {c}" for c in cpt]) if cpt else "None"

    return f"""
RECORD SUMMARY
--------------
Name: {patient.get("name","Kevin Smith")}
DOB: {patient.get("dob","Unknown")} | Age: {patient.get("age","Unknown")}
Gender: {patient.get("gender","Unknown")}
Race: {patient.get("race","Unknown")}
Height: {patient.get("height","Unknown")}
Weight: {patient.get("weight","Unknown")}

PROVIDERS
---------
{provider_lines}

DIAGNOSES
---------
{dx_lines}

ICD CODES
---------
{icd_lines}

CPT CODES
---------
{cpt_lines}

MEDICATIONS
-----------
{med_lines}
"""
