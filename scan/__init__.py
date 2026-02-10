import os
import json
import traceback

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
# OCR helpers
# -----------------------

def extract_page_text(result, page_index: int):

    page = result.pages[page_index]

    if not page.lines:
        return ""

    return "\n".join(line.content for line in page.lines)


# -----------------------
# Signature detection (LLM-based, Azure-native)
# -----------------------

def detect_signature(result):

    SIGNATURE_KEYWORDS = [
        "signature",
        "signed",
        "physician signature",
        "provider signature",
        "authorized signature",
        "signed by",
        "provider sign"
    ]

    signature_present = False
    signature_pages = []

    for page in result.pages:

        page_number = page.page_number

        keyword_regions = []
        handwriting_regions = []

        # Collect regions
        for line in page.lines or []:

            text = line.content.lower()

            polygon = line.polygon if hasattr(line, "polygon") else None

            if not polygon:
                continue

            # Check keyword regions
            if any(keyword in text for keyword in SIGNATURE_KEYWORDS):
                keyword_regions.append(polygon)

            # Check handwriting regions
            if hasattr(line, "appearance") and line.appearance:
                if getattr(line.appearance, "style_name", None) == "handwriting":
                    handwriting_regions.append(polygon)

        # Check if handwriting is near keyword
        for k_region in keyword_regions:
            for h_region in handwriting_regions:

                # Compare Y position (vertical proximity)
                keyword_y = k_region[1]
                handwriting_y = h_region[1]

                if abs(keyword_y - handwriting_y) < 0.1:
                    signature_present = True
                    signature_pages.append(page_number)
                    break

            if signature_present:
                break

    return {
        "signature_present": signature_present,
        "pages": signature_pages
    }

# -----------------------
# Order extraction
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

    # OCR / layout analysis
    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    # Detect signature
    signature_info = detect_signature(result)

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
                    "OPENAI_ENDPOINT": bool(os.getenv("OPENAI_ENDPOINT")),
                    "OPENAI_KEY": bool(os.getenv("OPENAI_KEY")),
                    "OPENAI_DEPLOYMENT": bool(os.getenv("OPENAI_DEPLOYMENT")),
                    "DOC_INTEL_ENDPOINT": bool(os.getenv("DOC_INTEL_ENDPOINT")),
                    "DOC_INTEL_KEY": bool(os.getenv("DOC_INTEL_KEY"))
                }
            }),
            status_code=500,
            mimetype="application/json"
        )
