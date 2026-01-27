import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared.doc_intelligence import analyze_document


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        document_base64 = body.get("documentBase64")

        if not document_base64:
            return func.HttpResponse(
                json.dumps({ "error": "documentBase64 required" }),
                status_code=400,
                mimetype="application/json"
            )

        text = analyze_document(document_base64)

        return func.HttpResponse(
            json.dumps({
                "status": "ok",
                "ocr_preview": text[:1000]
            }),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": str(e),
                "type": type(e).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )
