import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts


def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    document_base64 = body.get("documentBase64")

    if not document_base64:
        return func.HttpResponse(
            json.dumps({"error": "documentBase64 required"}),
            status_code=400,
            mimetype="application/json"
        )

    # OCR
    text = analyze_document(document_base64)

    # LLM extraction
    facts = extract_medical_facts(text)

    # 🚨 HARD OVERRIDE: only return LLM output
    return func.HttpResponse(
        json.dumps({
            "PIPELINE_STAGE": "LLM_EXTRACTION",
            "facts": facts
        }, indent=2),
        mimetype="application/json"
    )
