import base64
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def analyze_document(document_base64: str) -> str:
    endpoint = os.environ.get("DOC_INTEL_ENDPOINT")
    key = os.environ.get("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise ValueError("DOC_INTEL_ENDPOINT or DOC_INTEL_KEY not set")

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    document_bytes = base64.b64decode(document_base64)

    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body=document_bytes
    )

    result = poller.result()

    lines = []
    for page in result.pages:
        for line in page.lines:
            lines.append(line.content)

    return "\n".join(lines)
