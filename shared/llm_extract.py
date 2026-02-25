import os
import json
from openai import AzureOpenAI


def extract_structured_data(ocr_text: str):

    endpoint = os.getenv("OPENAI_ENDPOINT")
    key = os.getenv("OPENAI_KEY")
    deployment = os.getenv("OPENAI_DEPLOYMENT")

    client = AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )

    prompt = f"""
Extract structured medical data.

Return ONLY valid JSON.

Schema:

{{
  "patient": {{
    "name": "Kevin Smith",
    "dob": null,
    "age": null,
    "gender": null,
    "race": null,
    "height": null,
    "weight": null
  }},
  "medications": [
    {{
      "name": "",
      "status": "active" | "inactive" | "unknown"
    }}
  ],
  "providers": [
    {{
      "name": "",
      "specialty": "",
      "address": ""
    }}
  ],
  "diagnoses": [],
  "icd_codes": [],
  "cpt_codes": [],
  "flags": {{
    "diabetes": false,
    "cancer": false,
    "copd": false,
    "chf": false,
    "heart_disease": false,
    "stroke": false
  }}
}}

Rules:
- Do NOT infer medications
- Extract ALL medications listed
- Mark status active/inactive if possible
- Do NOT include pharmacies
- Deduplicate ICD and CPT codes

OCR TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    structured = json.loads(content)

    # ✅ ADD THIS LINE
    structured["raw_text"] = ocr_text

    return structured
