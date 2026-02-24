import os
import json
import re
from openai import AzureOpenAI


# -----------------------
# Helpers
# -----------------------

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def medication_in_ocr(med: str, ocr_text: str) -> bool:
    """
    Ensures medication actually exists in OCR text
    Prevents hallucinations like Humalog
    """
    med_norm = normalize_text(med)
    ocr_norm = normalize_text(ocr_text)

    # Check full string
    if med_norm in ocr_norm:
        return True

    # Check base name (first word)
    base = med_norm.split()[0]
    if len(base) >= 4 and base in ocr_norm:
        return True

    return False


def clean_medications(raw_meds, ocr_text):

    if not isinstance(raw_meds, list):
        return []

    cleaned = []

    for med in raw_meds:
        if not isinstance(med, str):
            continue

        med_clean = med.strip()
        if not med_clean:
            continue

        # Only enforce: must exist in OCR
        if not medication_in_ocr(med_clean, ocr_text):
            continue

        cleaned.append(med_clean)

    # Deduplicate
    seen = set()
    final = []
    for m in cleaned:
        key = normalize_text(m)
        if key not in seen:
            seen.add(key)
            final.append(m)

    return final

# -----------------------
# Main extraction
# -----------------------

def extract_structured_data(ocr_text: str):

    if not ocr_text or len(ocr_text.strip()) < 20:
        raise RuntimeError("OCR text is empty or invalid.")

    endpoint = os.getenv("OPENAI_ENDPOINT")
    key = os.getenv("OPENAI_KEY")
    deployment = os.getenv("OPENAI_DEPLOYMENT")

    if not endpoint or not key or not deployment:
        raise RuntimeError("Missing OpenAI environment variables.")

    client = AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )

    prompt = f"""
You are extracting structured medical underwriting data.

Return ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.

STRICT RULES:
- Do NOT infer anything
- Only extract what is explicitly written
- If unsure, leave it null or false

MEDICATION RULES:
- Extract medications ONLY from a medication list
- DO NOT include short-term meds (e.g., antibiotics, injury meds)
- DO NOT guess medications (e.g., insulin for diabetes unless explicitly written)
- Chronic medications

IMPORTANT:
It is better to include too many medications than to miss medications.
We will filter later.

Schema:

{{
  "conditions": {{
    "diabetes_type": "type1" | "type2" | null,
    "asthma": boolean,
    "arthritis": boolean,
    "active_cancer": boolean
  }},
  "medications": [string],
  "has_stroke": boolean,
  "has_tia": boolean,
  "has_neuropathy": boolean,
  "has_retinopathy": boolean
}}

OCR TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Extract structured medical data. JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Empty LLM response.")

    content = content.strip()

    # Remove markdown if present
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    try:
        structured = json.loads(content)
    except Exception:
        raise RuntimeError(f"Invalid JSON from LLM:\n\n{content}")

    # -----------------------
    # 🔥 CRITICAL: ONE SOURCE OF TRUTH
    # -----------------------
    structured["medications"] = clean_medications(
        structured.get("medications", []),
        ocr_text
    )

    return structured
