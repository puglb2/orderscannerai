import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func
from shared.doc_intelligence import analyze_document

def main(req: func.HttpRequest) -> func.HttpResponse:
    result = analyze_document("test")

    return func.HttpResponse(
        json.dumps({ "status": result }),
        mimetype="application/json"
    )
