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
        raise RuntimeError("Missing DOC_INTEL environment variables")

    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )


def get_openai_client():

    endpoint = os.getenv("OPENAI_ENDPOINT")
    key = os.getenv("OPENAI_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing OPENAI environment variables")

    return AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version="2024-02-15-preview"
    )


# -----------------------
# OCR helper
# -----------------------

def extract_page_text(result, page_index):

    page = result.pages[page_index]

    if not page.lines:
        return ""

    return "\n".join(line.content for line in page.lines)


# -----------------------
# Render pages as images via Document Intelligence
# -----------------------

def extract_page_images(pdf_bytes):

    doc_client = get_doc_client()

    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes,
        output=["figures"]
    )

    result = poller.result()

    images = []

    if hasattr(result, "figures") and result.figures:

        for fig in result.figures:

            if hasattr(fig, "image") and fig.image:

                images.append(fig.image)

    return images


# -----------------------
# Vision signature detection
# -----------------------

def detect_signature(result):

    SIGNATURE_KEYWORDS = [
        "signature",
        "signed",
        "physician signature",
        "provider signature",
        "authorized signature"
    ]

    signature_found = False
    signature_pages = []

    for page in result.pages:

        page_number = page.page_number

        keyword_lines = []
        handwriting_lines = []

        for line in page.lines or []:

            text = line.content.lower()

            if any(keyword in text for keyword in SIGNATURE_KEYWORDS):
                keyword_lines.append(line)

            # check handwriting flag
            if hasattr(line, "appearance") and line.appearance:
                if getattr(line.appearance, "style_name", "") == "handwriting":
                    handwriting_lines.append(line)

        # only classify as signature if handwriting is near signature keyword
        for keyword_line in keyword_lines:

            keyword_polygon = keyword_line.polygon

            for hw_line in handwriting_lines:

                hw_polygon = hw_line.polygon

                # check vertical proximity (same area)
                if abs(hw_polygon[1] - keyword_polygon[1]) < 0.15:

                    signature_found = True
                    signature_pages.append(page_number)
                    break

    return {
        "signature_present": signature_found,
        "pages": signature_pages
    }


# -----------------------
# Order extraction
# -----------------------

def ask_openai_for_fields(page_number, page_text):

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
  "ordering_provider": null,
  "order_date": null,
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

def run_scanner(pdf_bytes):

    doc_client = get_doc_client()

    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    # Extract images for vision
    page_images = extract_page_images(pdf_bytes)

    signature_info = detect_signature(result)

    output = {
        "orders": [],
        "document_signature": signature_info
    }

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

def main(req):

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
