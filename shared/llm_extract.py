import json
import os
import requests
from shared.schema_v1 import MEDICAL_FACTS_SCHEMA_V1

SYSTEM_PROMPT = (
    "You are a medical document extraction engine.\n"
    "You do NOT make medical judgments.\n"
    "You do NOT infer missing information.\n"
    "You do NOT score risk.\n"
    "You ONLY extract facts explicitly stated in the text.\n"
    "If a value is not clearly present, return null or false.\n"
    "Output MUST be valid JSON matching the schema exactly.\n"
)

def build_prompt(ocr_text: str) -> str:
    return f"""
Extract medical facts from the OCR text below into the JSON schema.

Rules:
- Do NOT infer.
- Do NOT guess.
- Do NOT score.
- Use null if missing.
- Use "unknown" only when mentioned but unclear.
- Return ONLY JSON.

OCR TEXT:
<<<
{ocr_text}
>>>

JSON SCHEMA:
<<<
{json.dumps(MEDICAL_FACTS_SCHEMA_V1, indent=2)}
>>>
"""

def extract_medical_facts(ocr_text: str) -> dict:
    endpoint = os.environ["OPENAI_ENDPOINT"]
    key = os.environ["OPENAI_API_KEY"]
    deployment = os.environ["OPENAI_DEPLOYMENT"]

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(ocr_text)}
        ],
        "temperature": 0
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": key
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)
