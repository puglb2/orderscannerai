import os
import json
import re
from openai import AzureOpenAI


def _norm(s: str) -> str:
    """Normalize text for robust substring matching."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _med_base_name(med: str) -> str:
    """
    Try to reduce 'Humalog U-100 insulin' -> 'humalog'
    or 'Metoprolol tartrate 25 mg' -> 'metoprolol'
    """
    med_n = _norm(med)
    # take first token as base if it's meaningful
    parts = med_n.split()
    return parts[0] if parts else med_n


def _keep_only_meds_seen_in_ocr(meds: list, ocr_text: str) -> list:
    """
    Hard guardrail: only keep meds whose full normalized string OR base name
    appears in OCR text.
    """
    ocr_n = _norm(ocr_text)
    kept = []

    for m in meds or []:
        if not isinstance(m, str):
            continue
        m_stripped = m.strip()
        if not m_stripped:
            continue

        m_n = _norm(m_stripped)
        base = _med_base_name(m_stripped)

        # require literal evidence in OCR
        if m_n and m_n in ocr_n:
            kept.append(m_stripped)
            continue
        if base and len(base) >= 4 and base in ocr_n:
            kept.append(m_stripped)
            continue

        # else: drop it (likely inference/hallucination)

    # de-dupe while preserving order
    seen = set()
    out = []
    for m in kept:
        key = _norm(m)
        if key not in seen:
            seen.add(key)
            out.append(m)
    return out


def extract_structured_data(ocr_text: str):
    if not ocr_text or len(ocr_text.strip()) < 10:
        raise RuntimeError("OCR text is empty or too short.")

    endpoint = os.getenv("OPENAI_ENDPOINT")
    key = os.getenv("OPENAI_KEY")
    deployment = os.getenv("OPENAI_DEPLOYMENT")

    if not endpoint or not key or not deployment:
        raise RuntimeError("Missing OPENAI_ENDPOINT / OPENAI_KEY / OPENAI_DEPLOYMENT.")

    client = AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )

    prompt = f"""
You are extracting underwriting-relevant facts from OCR text.

Return ONLY valid JSON (no markdown, no commentary).

CRITICAL RULES:
- Do NOT infer medications. Only include meds explicitly listed as CURRENT/ACTIVE meds.
- Do NOT include acute one-off meds (e.g., antibiotics for injury/infection) unless clearly ongoing.
- If a med is mentioned as a past prescription or short course, exclude it.

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
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("LLM returned empty response.")

    # strip accidental code fences
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    structured = json.loads(content)

    # HARD guardrail: remove hallucinated meds by requiring literal OCR evidence
    meds = structured.get("medications", [])
    if not isinstance(meds, list):
        meds = []
    structured["medications"] = _keep_only_meds_seen_in_ocr(meds, ocr_text)

    return structured
