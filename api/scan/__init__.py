import os
import json
import base64
import tempfile

import azure.functions as func
import fitz  # PyMuPDF

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI


# --------------------------------------------------
# Azure clients (created once per function instance)
# --------------------------------------------------
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_DEPLOYMENT = os.getenv("OPENAI_DEPLOYMENT")
OPENAI_DEPLOYMENT_VISION = os.getenv("OPENAI_DEPLOYMENT_VISION")

def get_doc_client():
    return DocumentIntelligenceClient(
        endpoint=os.getenv("DOC_INTEL_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("DOC_INTEL_KEY"))
    )

def get_openai_client():
    return AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )

# --------------------------------------------------
# Helper functions (your existing logic)
# --------------------------------------------------
def extract_page_text(result, page_index: int) -> str:
    page = result.pages[page_index]
    if not page.lines:
        return ""
    return "\n".join(line.content for line in page.lines)


def ask_openai_for_fields(page_number: int, page_text: str) -> dict:
    prompt = (
        "Return ONLY valid JSON. No markdown. No extra text.\n\n"
        "Schema:\n"
        "{\n"
        '  "page_number": <int>,\n'
        '  "is_order": <true/false>,\n'
        '  "order_type": "lab"|"imaging"|"referral"|"other",\n'
        '  "tests_or_procedures": <array of strings>,\n'
        '  "icd10_codes": <array of strings>,\n'
        '  "cpt_codes": <array of strings>,\n'
        '  "ordering_provider": <string or null>,\n'
        '  "order_date": <string or null>,\n'
        '  "signature_present": <true/false>,\n'
        '  "notes": <string or null>,\n'
        '  "confidence": <number 0 to 1>\n'
        "}\n\n"
        "Rules:\n"
        "- Use ONLY info present in the text.\n"
        "- signature_present is TEXT ONLY for now.\n\n"
        f"PAGE NUMBER: {page_number}\n\n"
        f"PAGE TEXT:\n{page_text}"
    )

    resp = openai_client.chat.completions.create(
        model=OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a medical document field extractor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(resp.choices[0].message.content)


def detect_document_signature(pdf_path: str, max_pages: int = 10) -> dict:
    doc = fitz.open(pdf_path)
    pages_to_check = min(doc.page_count, max_pages)

    for i in range(pages_to_check):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        png_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")

        resp = openai_client.chat.completions.create(
            model=OPENAI_DEPLOYMENT_VISION,
            messages=[
                {
                    "role": "system",
                    "content": "Detect handwritten signature scribbles. Return JSON only."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Is there a handwritten signature scribble on this page?\n\n"
                                "Return JSON:\n"
                                "{\n"
                                '  "signature_present": true/false,\n'
                                '  "reason": "<short>"\n'
                                "}"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{png_b64}"}
                        }
                    ]
                }
            ]
        )

        data = json.loads(resp.choices[0].message.content)
        if data.get("signature_present") is True:
            return {
                "signature_present": True,
                "page_number": i + 1,
                "reason": data.get("reason", "")
            }

    return {
        "signature_present": False,
        "page_number": None,
        "reason": "No handwritten signature detected."
    }


# --------------------------------------------------
# Core scanner logic (formerly your local main())
# --------------------------------------------------
def run_scanner(pdf_path: str) -> dict:
    with open(pdf_path, "rb") as f:
        poller = doc_client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()

    out = {
        "orders": []
    }

    for i in range(len(result.pages)):
        page_number = result.pages[i].page_number
        page_text = extract_page_text(result, i)

        if not page_text.strip():
            continue

        fields = ask_openai_for_fields(page_number, page_text)
        if fields.get("is_order") is True:
            out["orders"].append(fields)

    out["document_signature"] = detect_document_signature(pdf_path)

    return out


# --------------------------------------------------
# Azure Function entry point
# --------------------------------------------------
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    try:
        pdf_bytes = req.get_body()
        if not pdf_bytes:
            return func.HttpResponse("No PDF provided", status_code=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            pdf_path = tmp.name

        result = run_scanner(pdf_path)

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
