import azure.functions as func
import traceback


def main(req: func.HttpRequest) -> func.HttpResponse:

    try:

        mode = req.form.get("mode")
        file = req.files.get("file")

        if not file:
            return func.HttpResponse(
                "No file uploaded.",
                status_code=400
            )

        pdf_bytes = file.read()

        from shared.doc_intelligence import analyze_document
        from shared.llm_extract import extract_structured_data
        from shared.scoring import calculate_score
        from shared.clinical_summary import generate_clinical_summary

        ocr_text = analyze_document(pdf_bytes)

        structured = extract_structured_data(ocr_text)

        if mode == "summary":
            return func.HttpResponse(
                generate_clinical_summary(ocr_text),
                mimetype="text/plain"
            )

        elif mode == "score":

            result = calculate_score(structured)

            explanation = "\n".join(
                [f"• {driver}" for driver in result["drivers"]]
            )

            output_text = (
                f"INSURABILITY SCORE: {result['score']} / 10\n\n"
                f"Primary risk drivers:\n{explanation}"
            )

            return func.HttpResponse(
                output_text,
                mimetype="text/plain"
            )

        else:

            result = calculate_score(structured)
            summary = generate_clinical_summary(ocr_text)

            explanation = "\n".join(
                [f"• {driver}" for driver in result["drivers"]]
            )

            output_text = (
                summary +
                f"\n\nINSURABILITY SCORE: {result['score']} / 10\n\n"
                f"Primary risk drivers:\n{explanation}"
            )

            return func.HttpResponse(
                output_text,
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
