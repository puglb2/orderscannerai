import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared import doc_intelligence

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({ "status": "shared import OK" }),
        mimetype="application/json"
    )
