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
Return ONLY valid JSON.

Structure:

{{
  "conditions": {{
    "diabetes_type": null,
    "asthma": false,
    "arthritis": false,
    "active_cancer": false
  }},
  "medications": [],
  "has_stroke": false,
  "has_tia": false,
  "has_neuropathy": false,
  "has_retinopathy": false
}}

OCR TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You extract structured medical data and return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    # 🔥 Remove markdown fences if present
    if content.startswith("```"):
        content = content.split("```")[1]

    # 🔥 Defensive fallback
    try:
        return json.loads(content)
    except Exception:
        # If LLM fails, return safe empty structure
        return {
            "conditions": {
                "diabetes_type": None,
                "asthma": False,
                "arthritis": False,
                "active_cancer": False
            },
            "medications": [],
            "has_stroke": False,
            "has_tia": False,
            "has_neuropathy": False,
            "has_retinopathy": False
        }
