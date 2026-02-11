import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:

    return func.HttpResponse(
        "UnderwritingAI function is running correctly.",
        status_code=200,
        mimetype="text/plain"
    )
