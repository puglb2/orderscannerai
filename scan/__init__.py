import os
import json
import traceback
import base64

import azure.functions as func

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from openai import AzureOpenAI

import fitz  # PyMuPDF


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

def extract_page_text(result, page_index):

    page = result.pages[page_index]

    if not page.lines:
        return ""

    return "\n".join(line.content for line in page.lines)


# -----------------------
# Vision signature detection
# -----------------------

def detect_signature(pdf_bytes):

    client = get_openai_client()

    deployment = os.getenv("OPENAI_VISION_DEPLOYMENT")

    if not deployment:
        raise RuntimeError("OPENAI_VISION_DEPLOYMENT not set")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    signature_found = False
    signature_pages = []

    for page_index in range(len(doc)):

        page = doc.load_page(page_index)

        pix = page.get_pixmap(dpi=200)

        img_bytes = pix.tobytes("png")

        img_base64 = base64.b64encode(img_bytes).decode()

        prompt = """
Does this page contain a physician or provider signature?

A signature includes:
- cursive signature
- stylized scribble
- signature block
- electronic signature

Do NOT classify general handwriting as signature.

Respond ONLY with JSON:

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
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content.lower()

        if "true" in content:

            signature_found = True
            signature_pages.append(page_index + 1)

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

    signature_info = detect_signature(pdf_bytes)

    output = {
        "orders": [],
        "document_signature": signature_info
    }

    for i in range(len(result.pages)):

        page_text = extract_page_text(result, i)

        if not page_text.strip():
            continue

        fields = ask_openai_for_fields(i + 1, page_text)

        is_order = fields.get("is_order", False)

        has_medical_indicators = (
            fields.get("icd10_codes") or
            fields.get("tests_or_procedures") or
            fields.get("order_type")
        )

        if is_order or has_medical_indicators:

            if not fields.get("icd10_codes"):
                fields["icd10_codes"] = []

            fields["signature_present"] = signature_info.get("signature_present", False)

            fields["icd_status"] = (
                "found" if fields["icd10_codes"] else "not_found"
            )

            fields["signature_status"] = (
                "found" if fields["signature_present"] else "not_detected"
            )

            output["orders"].append(fields)

    # fallback if nothing detected
    if not output["orders"]:

        output["orders"].append({
            "page_number": 1,
            "is_order": False,
            "order_type": "unknown",
            "tests_or_procedures": [],
            "icd10_codes": [],
            "signature_present": signature_info.get("signature_present", False),
            "icd_status": "not_found",
            "signature_status": (
                "found" if signature_info.get("signature_present") else "not_detected"
            ),
            "notes": "No ICD codes detected."
        })

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
