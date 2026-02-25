import os
from openai import AzureOpenAI


# -----------------------
# LLM SUMMARY (uses full OCR)
# -----------------------
def generate_summary_paragraph(ocr_text):

    client = AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )

    prompt = f"""
Write a clear clinical summary of this medical record.

Requirements:
- 1–2 paragraphs
- Include key diagnoses and major conditions
- Mention important medications if relevant
- Mention major events (stroke, hospitalizations, complications)
- Do NOT include underwriting or scoring
- Do NOT use bullet points
- Do NOT hallucinate — only use what is in the record

Medical Record:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a clinical summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


# -----------------------
# MAIN SUMMARY BUILDER
# -----------------------
def generate_clinical_summary(structured):

    patient = structured.get("patient", {})
    meds = structured.get("medications", [])
    providers = structured.get("providers", [])
    diagnoses = structured.get("diagnoses", [])
    icd = list(set(structured.get("icd_codes", [])))
    cpt = list(set(structured.get("cpt_codes", [])))
    ocr_text = structured.get("raw_text", "")

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
bmi = {patient.get("bmi")}
smoking = {patient.get("smoking_status", "Unknown")}
"""

    # -----------------------
    # REAL SUMMARY (LLM)
    # -----------------------
    try:
        summary = generate_summary_paragraph(ocr_text)
    except Exception:
        summary = "Summary unavailable."

    # -----------------------
    # DIAG + ICD
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
        f"- {m.get('name')}"
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

    # -----------------------
    # FINAL OUTPUT
    # -----------------------
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
