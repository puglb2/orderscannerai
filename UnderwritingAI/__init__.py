import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import azure.functions as func

from shared.doc_intelligence import analyze_document
from shared.llm_extract import extract_medical_facts
from shared.scoring import compute_underwriting_score_v1
from shared.format_text import format_underwriting_text_llm


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        mode = body.get("mode", "both")          # summary | score | both
        output = body.get("output", "text")      # text | json
        document_base64 = body.get("documentBase64")

        if not document_base64:
            raise ValueError("documentBase64 missing")

        if mode not in ("summary", "score", "both"):
            raise ValueError("mode must be summary, score, or both")

        if output not in ("text", "json"):
            raise ValueError("output must be text or json")

        # 1) OCR
        ocr_text = analyze_document(document_base64)

        # 2) Extract facts (schema)
        facts = extract_medical_facts(ocr_text)

        # 3) Score (rules)
        score = compute_underwriting_score_v1(facts)

        # 4) LLM narrative (facts-only)
        narrative = format_underwriting_text_llm(facts, score)

        # TEXT OUTPUT (default)
        if output == "text":
            lines = []
            if mode in ("summary", "both"):
                lines.append("RECORD SUMMARY")
                lines.append("--------------")
                lines.append(narrative)
                lines.append("")

            if mode in ("score", "both"):
                lines.append("INSURABILITY SCORE")
                lines.append("------------------")
                lines.append(f"Score: {score.get('score')} / 10")
                lines.append("")
                lines.append("Score drivers:")
                for item in score.get("breakdown", []):
                    pts = item.get("points", 0)
                    sign = "+" if pts > 0 else ""
                    lines.append(f"- {item.get('item')} ({sign}{pts})")

            return func.HttpResponse("\n".join(lines).strip(), mimetype="text/plain")

        # JSON OUTPUT (optional/debug)
        response = {"status": "ok", "mode": mode}
        if mode in ("summary", "both"):
            response["summary"] = facts
            response["narrative"] = narrative
        if mode in ("score", "both"):
            response["insurability"] = score
        return func.HttpResponse(json.dumps(response, indent=2), mimetype="application/json")

    except Exception as e:
        # For production, we should remove trace returns and log a redacted error id instead.
        import traceback
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "type": type(e).__name__,
                "message": str(e),
                "trace": traceback.format_exc()
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )
