import json
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        return func.HttpResponse(
            json.dumps({
                "status": "BOOT_OK",
                "received_keys": list(body.keys())
            }, indent=2),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "ERROR",
                "type": type(e).__name__,
                "message": str(e)
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
