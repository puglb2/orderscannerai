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

MEDICATIONS
-----------
List all medications mentioned in the record.
If none found say "None documented."

PROVIDERS
---------
List all providers, doctors, clinics, or healthcare facilities mentioned.
If none found say "None documented."

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
