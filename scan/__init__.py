import os
import json
import base64
import tempfile

import azure.functions as func


# ---------- Lazy client creators ----------
def get_doc_client():
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    return DocumentIntelligenceClient(
        endpoint=os.getenv("DOC_INTEL_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("DOC_INTEL_KEY"))
    )


def get_openai_client():
    from openai import AzureOpenAI

    return AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )


# ---------- Helpers ----------
def extract_page_text(result, page_index: int) -> str:
    page = result.pages[page_index]
    if not page.lines:
        return ""
    return "\n".join(line.content for line in page.lines)


def ask_openai_for_fields(page_number: int, page_text: str) -> dict:
    client = get_openai_client()

    prompt = (
        "Return ONLY valid JSON.\n\n"
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
        f"PAGE NUMBER: {page_number}\n\n"
        f"PAGE TEXT:\n{page_text}"
    )

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "Extract structured medical order data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(resp.choices[0].message.content)


def detect_document_signature(pdf_path: str) -> dict:
    import fitz  # PyMuPDF

    client = get_openai_client()
    doc = fitz.open(pdf_path)

    for i in range(min(doc.page_count, 10)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_b64 = base64.b64encode(pix.tobytes("png")).decode()

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_VISION"),
            messages=[
                {
                    "role": "system",
                    "content": "Detect handwritten signature scribbles."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is there a handwritten signature scribble? Return JSON { signature_present: true/false }"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ]
        )

        result = json.loads(resp.choices[0].message.content)
        if result.get("signature_present"):
            return {"signature_present": True, "page": i + 1}

    return {"signature_present": False}


# ---------- Core scanner ----------
def run_scanner(pdf_path: str) -> dict:
    doc_client = get_doc_client()

    with open(pdf_path, "rb") as f:
        poller = doc_client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()

    output = {"orders": []}

    for i in range(len(result.pages)):
        text = extract_page_text(result, i)
        if not text.strip():
            continue

        fields = ask_openai_for_fields(i + 1, text)
        if fields.get("is_order"):
            output["orders"].append(fields)

    output["document_signature"] = detect_document_signature(pdf_path)
    return output


# ---------- Azure entry point ----------
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    try:
        pdf_bytes = req.get_body()
        if not pdf_bytes:
            return func.HttpResponse("No PDF uploaded", status_code=400)

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
    import traceback
    return func.HttpResponse(
        json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "env_check": {
                "OPENAI_ENDPOINT": bool(os.getenv("OPENAI_ENDPOINT")),
                "OPENAI_KEY": bool(os.getenv("OPENAI_KEY")),
                "DOC_INTEL_ENDPOINT": bool(os.getenv("DOC_INTEL_ENDPOINT")),
                "DOC_INTEL_KEY": bool(os.getenv("DOC_INTEL_KEY")),
            }
        }),
        status_code=500,
        mimetype="application/json"
    )
