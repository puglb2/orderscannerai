import os
import json
import traceback
import base64

import azure.functions as func

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from openai import AzureOpenAI


# -----------------------
# Clients
# -----------------------

def get_doc_client():

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing Document Intelligence environment variables")

    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )


def get_openai_client():

    endpoint = os.getenv("OPENAI_ENDPOINT")
    key = os.getenv("OPENAI_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing Azure OpenAI environment variables")

    return AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )


# -----------------------
# OCR helper
# -----------------------

def extract_page_text(result, page_index: int):

    page = result.pages[page_index]

    if not page.lines:
        return ""

    return "\n".join(line.content for line in page.lines)


# -----------------------
# Vision signature detection
# -----------------------

def detect_signature_vision(pdf_bytes):

    client = get_openai_client()

    deployment = os.getenv("OPENAI_VISION_DEPLOYMENT")

    if not deployment:
        raise RuntimeError("OPENAI_VISION_DEPLOYMENT not set")

    pdf_base64 = base64.b64encode(pdf_bytes).decode()

    prompt = """
Determine whether this medical document contains a physician or provider signature.

A valid signature includes:
- handwritten cursive name
- stylized signature scribble
- provider signature block
- electronic signature

Do NOT classify handwritten notes as signatures unless clearly intended as one.

Respond ONLY in JSON format:

{
  "signature_present": true or false,
  "confidence": 0.0 to 1.0
}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:application/pdf;base64,{pdf_base64}"
                        }
                    }
                ]
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
        return {
            "signature_present": bool(parsed.get("signature_present", False)),
            "confidence": float(parsed.get("confidence", 0))
        }
    except:
        return {
            "signature_present": "true" in content.lower(),
            "confidence": 0.5
        }


# -----------------------
# Order extraction
# -----------------------

def ask_openai_for_fields(page_number: int, page_text: str):

    client = get_openai_client()

    deployment = os.getenv("OPENAI_DEPLOYMENT")

    if not deployment:
        raise RuntimeError("OPENAI_DEPLOYMENT not set")

    prompt = f"""
Return ONLY valid JSON.

{{
  "page_number": {page_number},
  "is_order": true or false,
  "order_type": "lab" | "imaging" | "referral" | "other",
  "tests_or_procedures": [],
  "icd10_codes": [],
  "cpt_codes": [],
  "ordering_provider": null,
  "order_date": null,
  "signature_present": false,
  "notes": null,
  "confidence": 0.0
}}

PAGE TEXT:
{page_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "Extract structured medical order data."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


# -----------------------
# Core scanner
# -----------------------

def run_scanner(pdf_bytes: bytes):

    doc_client = get_doc_client()

    # OCR
    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    # Vision signature detection
    signature_info = detect_signature_vision(pdf_bytes)

    output = {
        "orders": [],
        "document_signature": signature_info
    }

    # Extract orders and ICD codes
    for i in range(len(result.pages)):

        page_text = extract_page_text(result, i)

        if not page_text.strip():
            continue

        fields = ask_openai_for_fields(i + 1, page_text)

        if fields.get("is_order"):

            fields["signature_present"] = signature_info["signature_present"]

            output["orders"].append(fields)

    return output


# -----------------------
# Azure entry point
# -----------------------

def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        pdf_bytes = req.get_body()

        if not pdf_bytes:
            return func.HttpResponse(
                json.dumps({"error": "No PDF uploaded"}),
                status_code=400,
                mimetype="application/json"
            )

        result = run_scanner(pdf_bytes)

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:

        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "env_check": {
                    "OPENAI_DEPLOYMENT": bool(os.getenv("OPENAI_DEPLOYMENT")),
                    "OPENAI_VISION_DEPLOYMENT": bool(os.getenv("OPENAI_VISION_DEPLOYMENT")),
                    "DOC_INTEL_ENDPOINT": bool(os.getenv("DOC_INTEL_ENDPOINT")),
                    "DOC_INTEL_KEY": bool(os.getenv("DOC_INTEL_KEY"))
                }
            }),
            status_code=500,
            mimetype="application/json"
        )
