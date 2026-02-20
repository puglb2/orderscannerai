import os
import json
from openai import AzureOpenAI


def extract_structured_data(ocr_text: str):

    if not ocr_text or len(ocr_text.strip()) < 10:
        raise RuntimeError("OCR text is empty or too short.")

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
You are a medical underwriting data extraction engine.

Return ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.
Do NOT include commentary.
Do NOT wrap in ```json.

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
            {"role": "system", "content": "Extract structured underwriting medical data and return strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("LLM returned empty response.")

    content = content.strip()

    # Remove markdown fences if model still adds them
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        structured = json.loads(content)
    except Exception as e:
        raise RuntimeError(
            "LLM returned invalid JSON.\n\nRaw Output:\n"
            + content
        )

    return structured
