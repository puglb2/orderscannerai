import azure.functions as func
import json

def main(req: func.HttpRequest, context: func.Context):
    return func.HttpResponse(
        json.dumps({"status": "ok"}),
        status_code=200,
        mimetype="application/json"
    )
