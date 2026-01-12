import os
import json
import base64
from dotenv import load_dotenv

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import fitz  # PyMuPDF

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_DEPLOYMENT = os.getenv("OPENAI_DEPLOYMENT")          # text extraction
OPENAI_DEPLOYMENT_VISION = os.getenv("OPENAI_DEPLOYMENT_VISION")  # signature vision

# --------------------------------------------------
# Clients
# --------------------------------------------------
doc_client = DocumentIntelligenceClient(
    endpoint=DOC_INTEL_ENDPOINT,
    credential=AzureKeyCredential(DOC_INTEL_KEY)
)

openai_client = AzureOpenAI(
    api_key=OPENAI_KEY,
    azure_endpoint=OPENAI_ENDPOINT,
    api_version="2024-02-15-preview"
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def extract_page_text(result, page_index: int) -> str:
    page = result.pages[page_index]
    if not page.lines:
        return ""
    return "\n".join(line.content for line in page.lines)


def ask_openai_for_fields(page_number: int, page_text: str) -> dict:
    """
    Extract order-related fields from ONE page (text-only).
    """
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
        "- Use ONLY information present in the text.\n"
        "- If unknown, use null or empty arrays.\n"
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
    """
    Per-document handwritten signature detection (vision-based).
    Returns True if ANY page contains a scribble signature.
    """
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
                    "content": (
                        "You detect handwritten signature scribbles on documents. "
                        "Return JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Is there a handwritten signature scribble on this page?\n\n"
                                "Return JSON exactly like:\n"
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
            ],
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
        "reason": "No handwritten signature detected on scanned pages."
    }

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    pdf_path = "sample.pdf"

    with open(pdf_path, "rb") as f:
        poller = doc_client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()

    out = {
        "file_name": os.path.basename(pdf_path),
        "orders": []
    }

    # ---- Per-page order extraction (unchanged logic)
    for i in range(len(result.pages)):
        page_number = result.pages[i].page_number
        page_text = extract_page_text(result, i)

        if not page_text.strip():
            continue

        fields = ask_openai_for_fields(page_number, page_text)

        if fields.get("is_order") is True:
            out["orders"].append(fields)

    # ---- Per-document signature detection (NEW)
    out["document_signature"] = detect_document_signature(
        pdf_path=pdf_path,
        max_pages=10
    )

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
