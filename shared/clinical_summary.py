import os
from openai import AzureOpenAI


def generate_summary_paragraph(ocr_text: str):

    client = AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": "Write a clean clinical summary of this medical record. Do NOT include scoring. Do NOT list bullet points."
            },
            {
                "role": "user",
                "content": ocr_text[:12000]  # prevent token overflow
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


def generate_clinical_summary(ocr_text, structured):

    patient = structured.get("patient", {})
    meds = structured.get("medications", [])
    providers = structured.get("providers", [])
    diagnoses = structured.get("diagnoses", [])
    icd = structured.get("icd_codes", [])
    cpt = structured.get("cpt_codes", [])

    # -----------------------
    # 🧠 REAL SUMMARY
    # -----------------------
    summary_text = generate_summary_paragraph(ocr_text)

    # -----------------------
    # FORMAT DIAG + ICD TOGETHER
    # -----------------------
    diag_lines = []

    for i, d in enumerate(diagnoses):
        code = icd[i] if i < len(icd) else ""
        if code:
            diag_lines.append(f"- {d} ({code})")
        else:
            diag_lines.append(f"- {d}")

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
    cpt_text = "\n".join(set(cpt)) if cpt else "None"

    return f"""
RECORD SUMMARY
--------------
Name: {patient.get("name","Kevin Smith")}
DOB: {patient.get("dob","Unknown")} | Age: {patient.get("age","Unknown")}
Gender: {patient.get("gender","Unknown")}
Race: {patient.get("race","Unknown")}
Height: {patient.get("height","Unknown")}
Weight: {patient.get("weight","Unknown")}

SUMMARY
-------
{summary_text}

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
