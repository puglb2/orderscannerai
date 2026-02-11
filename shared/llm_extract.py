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
Extract structured underwriting-relevant medical data.

Return ONLY valid JSON:

{
  "conditions": {
    "diabetes_type": null,
    "asthma": false,
    "arthritis": false,
    "active_cancer": false
  },
  "medications": [],
  "has_stroke": false,
  "has_tia": false,
  "has_neuropathy": false,
  "has_retinopathy": false
}

RECORD TEXT:
{ocr_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Extract structured medical data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
