import json
import azure.functions as func
from .normalize import extract_medical_facts
from .rules import calculate_score
from .summary import generate_summary

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        mode = body.get("mode")
        document_base64 = body.get("documentBase64")

        if not mode or not document_base64:
            return func.HttpResponse(
                "mode and documentBase64 are required",
                status_code=400
            )

        facts = extract_medical_facts(document_base64)

        response = {}

        if mode in ("summary", "both"):
            response["summary"] = generate_summary(facts)

        if mode in ("score", "both"):
            response["insurability"] = calculate_score(facts)

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
