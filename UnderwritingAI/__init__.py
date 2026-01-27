import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()

    return func.HttpResponse(
        json.dumps({
            "status": "parsed",
            "mode": body.get("mode")
        }),
        mimetype="application/json"
    )
