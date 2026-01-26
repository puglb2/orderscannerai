import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "ok",
            "message": "Function is reachable",
            "method": req.method,
            "content_length": len(req.get_body() or b"")
        }),
        status_code=200,
        mimetype="application/json"
    )
