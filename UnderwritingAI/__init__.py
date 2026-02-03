import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        "🔥 LLM PIPELINE TEST — IF YOU SEE THIS, DEPLOYMENT IS CORRECT 🔥",
        mimetype="text/plain"
    )
