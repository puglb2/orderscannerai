import base64
import os
import time
import requests


def analyze_document(document_base64: str) -> str:
    endpoint = os.environ.get("DOC_INTEL_ENDPOINT")
    key = os.environ.get("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise ValueError("DOC_INTEL_ENDPOINT or DOC_INTEL_KEY not set")

    url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2023-10-31-preview"

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/pdf"
    }

    document_bytes = base64.b64decode(document_base64)

    # Start analysis
    response = requests.post(url, headers=headers, data=document_bytes)

    if response.status_code != 202:
        raise RuntimeError(f"Analyze failed: {response.text}")

    # Poll result
    result_url = response.headers["operation-location"]

    while True:
        result_response = requests.get(
            result_url,
            headers={"Ocp-Apim-Subscription-Key": key}
        )

        result = result_response.json()

        status = result.get("status")
        if status == "succeeded":
            break
        if status == "failed":
            raise RuntimeError(f"OCR failed: {result}")

        time.sleep(0.5)

    # Extract text
    lines = []
    for page in result["analyzeResult"]["pages"]:
        for line in page.get("lines", []):
            lines.append(line["content"])

    return "\n".join(lines)
