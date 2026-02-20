import traceback
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        from shared.doc_intelligence import analyze_document

    except Exception as e:
        return func.HttpResponse(
            "IMPORT ERROR: doc_intelligence\n\n"
            + str(e) + "\n\n" + traceback.format_exc(),
            mimetype="text/plain"
        )

    try:

        from shared.llm_extract import extract_structured_data

    except Exception as e:
        return func.HttpResponse(
            "IMPORT ERROR: llm_extract\n\n"
            + str(e) + "\n\n" + traceback.format_exc(),
            mimetype="text/plain"
        )

    try:

        from shared.scoring import calculate_score

    except Exception as e:
        return func.HttpResponse(
            "IMPORT ERROR: scoring\n\n"
            + str(e) + "\n\n" + traceback.format_exc(),
            mimetype="text/plain"
        )

    try:

        from shared.clinical_summary import generate_clinical_summary

    except Exception as e:
        return func.HttpResponse(
            "IMPORT ERROR: clinical_summary\n\n"
            + str(e) + "\n\n" + traceback.format_exc(),
            mimetype="text/plain"
        )

    try:
        pdf_bytes = req.get_body()

# DEBUG: inspect first bytes
        if not pdf_bytes:
            return func.HttpResponse("No body received.", mimetype="text/plain")

        preview = pdf_bytes[:20]

        return func.HttpResponse(
            f"First 20 bytes: {preview}",
            mimetype="text/plain"
)
#        pdf_bytes = req.get_body()
#
#        if not pdf_bytes:
#            return func.HttpResponse("No document uploaded.", mimetype="text/plain")
#
#        ocr_text = analyze_document(pdf_bytes)
#
#        structured = extract_structured_data(ocr_text)
#
#        score = calculate_score(structured)
#
#        summary = generate_clinical_summary(ocr_text)
#
#        return func.HttpResponse(
#            summary
#            + "\n\nScore: "
#            + str(score.get("score")),
#            mimetype="text/plain"
#        )0

    except Exception as e:

        return func.HttpResponse(
            "RUNTIME ERROR\n\n"
            + str(e)
            + "\n\n"
            + traceback.format_exc(),
            mimetype="text/plain"
        )
