import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Show filesystem contents at runtime
        root = os.path.dirname(os.path.dirname(__file__))
        shared_path = os.path.join(root, "shared")

        files = {}
        if os.path.exists(shared_path):
            files["shared"] = os.listdir(shared_path)
        else:
            files["shared"] = "NOT FOUND"

        return func.HttpResponse(
            json.dumps({
                "status": "FS_CHECK",
                "root": root,
                "files": files
            }, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        import traceback
        return func.HttpResponse(
            json.dumps({
                "status": "ERROR",
                "type": type(e).__name__,
                "message": str(e),
                "trace": traceback.format_exc()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
