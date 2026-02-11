import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def analyze_document(pdf_bytes: bytes) -> str:

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

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
