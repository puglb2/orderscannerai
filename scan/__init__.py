import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        pdf_bytes = req.get_body()

        return func.HttpResponse(
            json.dumps({
                "status": "scan function alive",
                "bytes_received": len(pdf_bytes) if pdf_bytes else 0
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
