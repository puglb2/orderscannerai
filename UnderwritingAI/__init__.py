import json
import traceback
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.scoring import calculate_score
from shared.clinical_summary import generate_clinical_summary


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        pdf_bytes = req.get_body()

        if not pdf_bytes:
            return func.HttpResponse(
                json.dumps({"error": "No document uploaded"}),
                status_code=400
            )

        ocr_text = analyze_document(pdf_bytes)

        structured = extract_structured_data(ocr_text)

        score = calculate_score(structured)

        clinical_summary = generate_clinical_summary(ocr_text)

        response = {
            "status": "ok",
            "clinical_summary": clinical_summary,
            "insurability": score
        }

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:

        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }),
            status_code=500
        )
