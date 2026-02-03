import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts
from shared.scoring import compute_underwriting_score_v1
from shared.format_text import (
    generate_record_summary_llm,
    generate_underwriting_explanation_llm
)


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        mode = body.get("mode", "both")
        output = body.get("output", "text")
        document_base64 = body.get("documentBase64")

        if not document_base64:
            raise ValueError("documentBase64 missing")

        if mode not in ("summary", "score", "both"):
            raise ValueError("Invalid mode")

        # OCR
        ocr_text = analyze_document(document_base64)

        # LLM extraction
        facts = extract_medical_facts(ocr_text)

        # Scoring
        score = compute_underwriting_score_v1(facts)

        # Text outputs
        summary_text = generate_record_summary_llm(facts)
        underwriting_text = generate_underwriting_explanation_llm(facts, score)

        if output == "text":
            sections = []

            if mode in ("summary", "both"):
                sections.append("RECORD SUMMARY")
                sections.append("--------------")
                sections.append(summary_text)

            if mode in ("score", "both"):
                sections.append("")
                sections.append("INSURABILITY ASSESSMENT")
                sections.append("------------------------")
                sections.append(underwriting_text)
                sections.append("")
                sections.append(f"Final insurability score: {score['score']} / 10")

            return func.HttpResponse(
                "\n".join(sections).strip(),
                mimetype="text/plain"
            )

        # JSON (optional)
        return func.HttpResponse(
            json.dumps({
                "summary": summary_text,
                "underwriting": underwriting_text,
                "score": score
            }, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        import traceback
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": str(e),
                "trace": traceback.format_exc()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
