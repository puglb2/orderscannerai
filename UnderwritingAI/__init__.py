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
                "Error: No document uploaded.",
                status_code=400,
                mimetype="text/plain"
            )

        # Step 1: OCR
        try:
            ocr_text = analyze_document(pdf_bytes)
        except Exception as e:
            return func.HttpResponse(
                "OCR ERROR:\n\n" + str(e) + "\n\n" + traceback.format_exc(),
                status_code=500,
                mimetype="text/plain"
            )

        # Step 2: Structured extraction
        try:
            structured_data = extract_structured_data(ocr_text)
        except Exception as e:
            return func.HttpResponse(
                "EXTRACTION ERROR:\n\n" + str(e) + "\n\n" + traceback.format_exc(),
                status_code=500,
                mimetype="text/plain"
            )

        # Step 3: Scoring
        try:
            insurability = calculate_score(structured_data)
        except Exception as e:
            return func.HttpResponse(
                "SCORING ERROR:\n\n" + str(e) + "\n\n" + traceback.format_exc(),
                status_code=500,
                mimetype="text/plain"
            )

        # Step 4: Summary
        try:
            clinical_summary = generate_clinical_summary(ocr_text)
        except Exception as e:
            return func.HttpResponse(
                "SUMMARY ERROR:\n\n" + str(e) + "\n\n" + traceback.format_exc(),
                status_code=500,
                mimetype="text/plain"
            )

        # Step 5: Build readable score section
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
            "CRITICAL FUNCTION ERROR:\n\n"
            + str(e)
            + "\n\nTRACEBACK:\n\n"
            + traceback.format_exc(),
            status_code=500,
            mimetype="text/plain"
        )
