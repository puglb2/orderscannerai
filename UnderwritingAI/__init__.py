import traceback
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_structured_data
from shared.scoring import calculate_score
from shared.clinical_summary import generate_clinical_summary


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        # Get PDF bytes
        pdf_bytes = req.get_body()

        if not pdf_bytes:
            return func.HttpResponse(
                "Error: No document uploaded.",
                status_code=400
            )

        # Step 1: OCR
        ocr_text = analyze_document(pdf_bytes)

        if not ocr_text.strip():
            return func.HttpResponse(
                "Error: No readable text found in document.",
                status_code=400
            )

        # Step 2: Structured extraction for scoring
        structured_data = extract_structured_data(ocr_text)

        # Step 3: Calculate score
        insurability = calculate_score(structured_data)

        # Step 4: Generate neutral clinical summary
        clinical_summary = generate_clinical_summary(ocr_text)

        # Step 5: Build readable score section
        score_text = "\n\nINSURABILITY SCORE\n------------------\n"
        score_text += f"Score: {insurability['score']} / 10\n\n"

        if insurability.get("breakdown"):
            score_text += "Contributing factors:\n"
            for item in insurability["breakdown"]:
                score_text += f"- {item}\n"

        # Final readable output
        final_output = clinical_summary + score_text

        return func.HttpResponse(
            final_output,
            status_code=200,
            mimetype="text/plain"
        )

    except Exception as e:

        return func.HttpResponse(
            "Error processing document:\n\n"
            + str(e)
            + "\n\n"
            + traceback.format_exc(),
            status_code=500,
            mimetype="text/plain"
        )
