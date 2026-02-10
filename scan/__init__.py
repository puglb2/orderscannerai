import os
import json
import base64
import traceback
import tempfile
from io import BytesIO

import azure.functions as func

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from openai import AzureOpenAI

from pdf2image import convert_from_bytes


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
# PDF → image conversion (in memory)
# -----------------------

def pdf_bytes_to_base64_images(pdf_bytes: bytes):

    images = convert_from_bytes(pdf_bytes, dpi=200)

    base64_images = []

    for img in images:

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        base64_images.append(
            base64.b64encode(buffer.getvalue()).decode()
        )

    return base64_images


# -----------------------
# Vision signature detection
# -----------------------

def detect_signature_vision(base64_image: str):

    client = get_openai_client()
    deployment = os.getenv("OPENAI_DEPLOYMENT")

    prompt = """
Determine if this medical document page contains a handwritten or drawn signature.

Respond ONLY in JSON format:

{
  "signature_present": true or false
}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content.lower()

    return "true" in result


# -----------------------
# OCR helpers
# -----------------------

def extract_page_text(result, page_index: int):

    page = result.pages[page_index]

    if not page.lines:
        return ""

    return "\n".join(line.content for line in page.lines)


# -----------------------
# ICD / order extraction
# -----------------------

def ask_openai_for_fields(page_number: int, page_text: str):

    client = get_openai_client()
    deployment = os.getenv("OPENAI_DEPLOYMENT")

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

    # OCR analysis
    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    # Vision signature detection
    base64_images = pdf_bytes_to_base64_images(pdf_bytes)

    signature_present = False

    for img in base64_images:

        if detect_signature_vision(img):
            signature_present = True
            break

    output = {
        "orders": [],
        "document_signature": {
            "signature_present": signature_present
        }
    }

    # Extract order data
    for i in range(len(result.pages)):

        page_text = extract_page_text(result, i)

        if not page_text.strip():
            continue

        fields = ask_openai_for_fields(i + 1, page_text)

        if fields.get("is_order"):

            fields["signature_present"] = signature_present

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
                "traceback": traceback.format_exc()
            }),
            status_code=500,
            mimetype="application/json"
        )
