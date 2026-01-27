import json
import azure.functions as func
from shared import doc_intelligence

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({ "status": "shared import OK" }),
        mimetype="application/json"
    )
