import os
from openai import AzureOpenAI


def generate_clinical_summary(ocr_text):

    client = AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )

    prompt = f"""
Summarize this medical record clearly.

Include:

1. Patient demographics:
   - Name (Kevin Smith if not found)
   - DOB, Age
   - Gender, Race
   - Height, Weight (if available)

2. A clean paragraph summary of the patient's condition

3. Diagnoses (include ICD codes if present, no duplicates)

4. Medications (include ALL listed, mark active/inactive if possible)

5. Providers (include name, specialty, and address if available)

6. CPT codes (no duplicates)

Rules:
- Do NOT include underwriting score
- Do NOT hallucinate
- Keep it clean and readable

Medical Record:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "You are a medical record summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
