# -----------------------
# SUMMARY ONLY
# -----------------------
if mode == "summary":
    return func.HttpResponse(
        generate_clinical_summary(ocr_text),
        mimetype="text/plain"
    )

# -----------------------
# SCORE ONLY
# -----------------------
if mode == "score":
    score, explanation = calculate_score(structured)

    return func.HttpResponse(
        f"INSURABILITY SCORE: {score}/10\n\nPrimary drivers:\n{explanation}",
        mimetype="text/plain"
    )

# -----------------------
# BOTH
# -----------------------
summary = generate_clinical_summary(ocr_text, structured)
score, explanation = calculate_score(structured)

output = f"""
{summary}

INSURABILITY SCORE: {score}/10

Primary drivers:
{explanation}
"""

return func.HttpResponse(output, mimetype="text/plain")
