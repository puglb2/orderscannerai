# SUMMARY
if mode == "summary":
    return func.HttpResponse(
        generate_clinical_summary(structured),
        mimetype="text/plain"
    )

# SCORE
if mode == "score":
    score, explanation = calculate_score(structured)

    return func.HttpResponse(
        f"INSURABILITY SCORE: {score}/10\n\nPrimary drivers:\n{explanation}",
        mimetype="text/plain"
    )

# BOTH
summary = generate_clinical_summary(structured)
score, explanation = calculate_score(structured)

return func.HttpResponse(
    f"{summary}\n\nINSURABILITY SCORE: {score}/10\n\nPrimary drivers:\n{explanation}",
    mimetype="text/plain"
)
