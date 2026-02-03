import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts


def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    mode = body.get("mode")
    document_base64 = body.get("documentBase64")

    if not document_base64:
        return func.HttpResponse(
            json.dumps({ "error": "documentBase64 required" }),
            status_code=400,
            mimetype="application/json"
        )

    # OCR
    text = analyze_document(document_base64)

    # LLM extraction
    facts = extract_medical_facts(text)

    # TEMP: just return facts until scoring is wired
    return func.HttpResponse(
        json.dumps({
            "stage": "EXTRACTION_COMPLETE",
            "facts": facts
        }, indent=2),
        mimetype="application/json"
    )
