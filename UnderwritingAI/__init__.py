import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        document_base64 = body.get("documentBase64")

        if not document_base64:
            raise ValueError("documentBase64 missing")

        # STEP 1 — OCR
        ocr_text = analyze_document(document_base64)

        # STEP 2 — LLM extraction
        facts = extract_medical_facts(ocr_text)

        return func.HttpResponse(
            json.dumps({
                "status": "LLM_OK",
                "facts": facts
            }, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        import traceback
        return func.HttpResponse(
            json.dumps({
                "status": "ERROR",
                "type": type(e).__name__,
                "message": str(e),
                "trace": traceback.format_exc()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
