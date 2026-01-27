import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "NEW FUNCTION APP CONFIRMED",
            "app": "famrsummaryscore",
        }),
        mimetype="application/json"
    )
