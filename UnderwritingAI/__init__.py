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
            raise ValueError("documentBase64 missing")

        ocr_text = analyze_document(document_base64)

        return func.HttpResponse(
            json.dumps({
                "status": "OCR_OK",
                "ocr_preview": ocr_text[:500]
            }, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "ERROR",
                "type": type(e).__name__,
                "message": str(e)
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
