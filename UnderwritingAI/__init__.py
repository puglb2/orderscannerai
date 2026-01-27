import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()

    return func.HttpResponse(
        json.dumps({
            "status": "PARSE_OK",
            "keys": list(body.keys())
        }),
        mimetype="application/json"
    )
