import json
import base64
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.clinical_summary import generate_clinical_summary
from shared.scoring import calculate_score


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:
        content_type = req.headers.get("Content-Type", "")

        # -----------------------
        # HANDLE JSON (base64)
        # -----------------------
        if "application/json" in content_type:

            body = req.get_json()
            mode = body.get("mode", "both")
            pdf_base64 = body.get("documentBase64")

            if not pdf_base64:
                return func.HttpResponse("Missing documentBase64", status_code=400)

            pdf_bytes = base64.b64decode(pdf_base64)

        # -----------------------
        # HANDLE RAW PDF
        # -----------------------
        else:
            mode = req.params.get("mode", "both")
            pdf_bytes = req.get_body()

            if not pdf_bytes:
                return func.HttpResponse("No PDF received", status_code=400)

        # -----------------------
        # PROCESS
        # -----------------------
        ocr_text = analyze_document(pdf_bytes)
        structured = extract_structured_data(ocr_text)

        # -----------------------
        # SUMMARY
        # -----------------------
        if mode == "summary":
            return func.HttpResponse(
                generate_clinical_summary(structured),
                mimetype="text/plain"
            )

        # -----------------------
        # SCORE
        # -----------------------
        if mode == "score":
            score, explanation = calculate_score(structured)

            return func.HttpResponse(
                f"INSURABILITY SCORE: {score}/10\n\nPrimary drivers:\n{explanation}",
                mimetype="text/plain"
            )

        # -----------------------
        # BOTH
        # -----------------------
        summary = generate_clinical_summary(structured)
        score, explanation = calculate_score(structured)

        output = f"""
{summary}

INSURABILITY SCORE: {score}/10

Primary drivers:
{explanation}
"""

        return func.HttpResponse(output, mimetype="text/plain")

    except Exception as e:
        return func.HttpResponse(
            f"Error processing underwriting request.\n\n{str(e)}",
            status_code=500
        )
