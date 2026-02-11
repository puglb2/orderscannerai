import traceback
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.scoring import calculate_score

# SAFE import of summary
try:
    from shared.clinical_summary import generate_clinical_summary
except Exception:
    generate_clinical_summary = None


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        pdf_bytes = req.get_body()

        if not pdf_bytes:
            return func.HttpResponse(
                "Error: No document uploaded.",
                status_code=400,
                mimetype="text/plain"
            )

        # OCR
        ocr_text = analyze_document(pdf_bytes)

        if not ocr_text.strip():
            return func.HttpResponse(
                "Error: No readable text found.",
                status_code=400,
                mimetype="text/plain"
            )

        # Extraction
        structured_data = extract_structured_data(ocr_text)

        # Scoring
        insurability = calculate_score(structured_data)

        # Summary (safe fallback)
        if generate_clinical_summary:
            try:
                clinical_summary = generate_clinical_summary(ocr_text)
            except Exception:
                clinical_summary = (
                    "RECORD SUMMARY\n--------------\n"
                    "Summary unavailable.\n"
                )
        else:
            clinical_summary = (
                "RECORD SUMMARY\n--------------\n"
                "Summary module not loaded.\n"
            )

        # Score section
        score_text = "\n\nINSURABILITY SCORE\n------------------\n"
        score_text += f"Score: {insurability.get('score', 'Unknown')} / 10\n\n"

        if insurability.get("breakdown"):
            score_text += "Contributing factors:\n"
            for item in insurability["breakdown"]:
                score_text += f"- {item}\n"

        final_output = clinical_summary + score_text

        return func.HttpResponse(
            final_output,
            status_code=200,
            mimetype="text/plain"
        )

    except Exception as e:

        return func.HttpResponse(
            "Error processing underwriting request.\n\n"
            + str(e)
            + "\n\n"
            + traceback.format_exc(),
            status_code=500,
            mimetype="text/plain"
        )
