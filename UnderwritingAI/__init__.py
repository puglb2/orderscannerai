import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared.doc_intelligence import analyze_document
from shared.normalize import normalize_medical_facts
from shared.rules import apply_rule_zero
from shared.scoring import compute_insurability_score


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        mode = body.get("mode")
        document_base64 = body.get("documentBase64")

        if not document_base64:
            return func.HttpResponse(
                json.dumps({ "error": "documentBase64 required" }),
                status_code=400,
                mimetype="application/json"
            )

        text = analyze_document(document_base64)
        facts = normalize_medical_facts(text)
        rule_zero = apply_rule_zero(facts)

        response = {
            "eligible": rule_zero["eligible"]
        }

        if mode in ("summary", "both"):
            response["summary"] = facts

        if mode in ("score", "both") and rule_zero["eligible"]:
            response["insurability"] = compute_insurability_score(facts)

        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )
