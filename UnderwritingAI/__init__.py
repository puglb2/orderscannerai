import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts
from shared.scoring import compute_underwriting_score_v1


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        mode = body.get("mode", "both")
        document_base64 = body.get("documentBase64")

        if not document_base64:
            raise ValueError("documentBase64 missing")

        if mode not in ("summary", "score", "both"):
            raise ValueError("mode must be summary, score, or both")

        ocr_text = analyze_document(document_base64)
        facts = extract_medical_facts(ocr_text)
        score = compute_underwriting_score_v1(facts)

        response = {
            "status": "ok",
            "mode": mode
        }

        if mode in ("summary", "both"):
            response["summary"] = facts

        if mode in ("score", "both"):
            response["insurability"] = score

        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        import traceback
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "type": type(e).__name__,
                "message": str(e),
                "trace": traceback.format_exc()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
