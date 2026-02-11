import os
import json
from openai import AzureOpenAI


def get_openai_client():

    return AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )


def extract_structured_data(ocr_text: str):

    client = get_openai_client()

    deployment = os.getenv("OPENAI_DEPLOYMENT")

    prompt = f"""
You are extracting structured clinical facts from a medical record.

Extract ALL clinical facts present.

DO NOT limit extraction to specific diseases.

Return ONLY valid JSON:

{{
  "conditions": [
    {{
      "name": "",
      "status": "active | history | resolved"
    }}
  ],
  "medications": [
    {{
      "name": "",
      "type": "medication"
    }}
  ],
  "providers": [
    {{
      "name": "",
      "type": "physician | clinic | hospital"
    }}
  ],
  "clinical_events": [
    {{
      "event": "",
      "type": "diagnosis | hospitalization | procedure"
    }}
  ]
}}

RECORD TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Extract clinical structured data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
