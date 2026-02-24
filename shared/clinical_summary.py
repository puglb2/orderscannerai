import os
from openai import AzureOpenAI


def get_openai_client():

    return AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )


def generate_clinical_summary(ocr_text: str):

    client = get_openai_client()

    deployment = os.getenv("OPENAI_DEPLOYMENT")

    meds = structured.get("medications", [])

    med_text = ", ".join(meds[:10]) if meds else "No active medications identified"
    
    prompt = f"""
You are a clinical documentation summarizer.

Your task is to summarize this medical record neutrally and factually.

DO NOT explain risk say underwriting or mention scoring.

DO NOT infer conditions not explicitly present.

DO NOT speculate.

OUTPUT FORMAT EXACTLY:

RECORD SUMMARY
--------------
Write a clear clinical summary of what this record contains.

Include the name of the patient in the summary.

MEDICATIONS
-----------
Put the number of medications in the header. EXAMPLE: MEDICATIONS (3)

List all medications mentioned in the record.
If none found say "None documented."

Extract ONLY medications that are explicitly listed as CURRENT or ACTIVE medications.

Include ONLY if:
- Listed under "Medications", "Current Medications", or similar section
- Clearly part of ongoing treatment

DO NOT include:
- Short-term prescriptions (e.g., antibiotics like amoxicillin)
- Medications prescribed for temporary conditions (injury, infection, etc.)
- Historical medications
- Medications mentioned in passing
- ANY inferred medications (e.g., insulin for diabetes unless explicitly listed)

STRICT RULE:
If a medication is not explicitly written as an active medication, DO NOT include it.

Return medications exactly as written. Do not guess or infer.

Medications:
{med_text}

PROVIDERS
---------
Only include individual medical providers.

Include:
- Physicians (MD, DO)
- Nurse Practitioners (NP)
- Physician Assistants (PA)
- Specialists (Cardiologist, Neurologist, etc.)

Format:
- Name (Specialty)

Examples:
- Dr. John Smith (Cardiologist)
- Jane Doe, NP (Primary Care)

Do NOT include:
- Pharmacies (CVS, Walgreens, Walmart)
- Facilities without a named provider
- Hospitals or organizations alone
- Locations or addresses"

RECORD TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You summarize medical records."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content
