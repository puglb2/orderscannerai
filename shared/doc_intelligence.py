import os
import base64

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def analyze_document(pdf_input) -> str:

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

    # Detect base64 vs raw bytes
    if isinstance(pdf_input, bytes):

        # Check if it's actually base64 text disguised as bytes
        try:
            decoded = base64.b64decode(pdf_input, validate=True)

            # Check if decoded result looks like PDF
            if decoded.startswith(b"%PDF"):
                pdf_bytes = decoded
            else:
                pdf_bytes = pdf_input

        except Exception:
            pdf_bytes = pdf_input

    elif isinstance(pdf_input, str):

        pdf_bytes = base64.b64decode(pdf_input)

    else:
        raise RuntimeError("Unsupported document input type")

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes
    )

    result = poller.result()

    full_text = []

    for page in result.pages:
        if page.lines:
            for line in page.lines:
                full_text.append(line.content)

    return "\n".join(full_text)
