import json
import azure.functions as func
from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.clinical_summary import generate_clinical_summary
from shared.scoring import calculate_score


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:
        body = req.get_json()
        mode = body.get("mode", "both")

        pdf_base64 = body.get("documentBase64")

        if not pdf_base64:
            return func.HttpResponse("No document provided", status_code=400)

        ocr_text = analyze_document(pdf_base64)
        structured = extract_structured_data(ocr_text)

        # -----------------------
        # SUMMARY ONLY
        # -----------------------
        if mode == "summary":
            summary = generate_clinical_summary(structured)
            return func.HttpResponse(summary, mimetype="text/plain")

        # -----------------------
        # SCORE ONLY
        # -----------------------
        if mode == "score":
            score, explanation = calculate_score(structured)

            output = f"""
INSURABILITY SCORE: {score}/10

Primary drivers:
{explanation}
"""
            return func.HttpResponse(output, mimetype="text/plain")

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
