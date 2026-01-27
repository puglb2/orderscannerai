import base64
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def analyze_document(document_base64: str) -> str:
    """
    Sends a Base64 PDF to Azure Document Intelligence (prebuilt-read)
    and returns extracted text.
    """

    endpoint = os.environ["DOC_INTEL_ENDPOINT"]
    key = os.environ["DOC_INTEL_KEY"]

    client = DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    document_bytes = base64.b64decode(document_base64)

    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        document=document_bytes
    )

    result = poller.result()

    text_lines = []
    for page in result.pages:
        for line in page.lines:
            text_lines.append(line.content)

    return "\n".join(text_lines)
