import traceback
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.scoring import calculate_score

# IMPORTANT: import summary safely
try:
    from shared.clinical_summary import generate_clinical_summary
except Exception as import_error:

    def generate_clinical_summary(text):
        return (
            "RECORD SUMMARY\n--------------\n"
            "Summary generation failed.\n\n"
            f"Import error:\n{str(import_error)}"
        )


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        pdf_bytes = req.get_body()

        if not pdf_bytes:
            return func.HttpResponse(
                "Error: No document uploaded.",
                status_code=400
            )

        # OCR
        ocr_text = analyze_document(pdf_bytes)

        if not ocr_text.strip():
            return func.HttpResponse(
                "Error: No readable text found.",
                status_code=400
            )

        # Structured extraction
        structured_data = extract_structured_data(ocr_text)

        # Score
        insurability = calculate_score(structured_data)

        # Summary (SAFE)
        try:
            clinical_summary = generate_clinical_summary(ocr_text)
        except Exception as summary_error:
            clinical_summary = (
                "RECORD SUMMARY\n--------------\n"
                "Summary generation failed.\n\n"
                f"Error:\n{str(summary_error)}\n\n"
                f"Traceback:\n{traceback.format_exc()}"
            )

        # Score section
        score_text = "\n\nINSURABILITY SCORE\n------------------\n"
        score_text += f"Score: {insurability.get('score', 'Unknown')} / 10\n\n"

        if insurability.get("breakdown"):
            score_text += "Contributing factors:\n"
            for item in insurability["breakdown"]:
                score_text += f"- {item}\n"

        output = clinical_summary + score_text

        return func.HttpResponse(
            output,
            status_code=200,
            mimetype="text/plain"
        )

    except Exception as e:

        return func.HttpResponse(
            "FULL ERROR:\n\n"
            + str(e)
            + "\n\nTRACEBACK:\n\n"
            + traceback.format_exc(),
            status_code=500,
            mimetype="text/plain"
        )
