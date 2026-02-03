import os
import json
import requests
import re


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise ValueError(f"Missing env var: {name}")
    return v


def _azure_openai_chat(messages, temperature=0.2, max_tokens=500) -> str:
    endpoint = _require_env("OPENAI_ENDPOINT").rstrip("/")
    api_key = _require_env("OPENAI_API_KEY")
    deployment = _require_env("OPENAI_DEPLOYMENT")
    api_version = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    r = requests.post(url, headers=headers, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _paragraphize(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    paragraphs = []
    for i in range(0, len(sentences), 2):
        paragraphs.append(" ".join(sentences[i:i+2]))
    return "\n\n".join(paragraphs)


# ------------------------------------------------------------------
# 1) PURE MEDICAL RECORD SUMMARY (NO SCORING, NO RISK LANGUAGE)
# ------------------------------------------------------------------

def generate_record_summary_llm(facts: dict) -> str:
    system = (
        "You are a clinical documentation assistant.\n"
        "Write a neutral, factual medical record summary.\n\n"
        "STRICT RULES:\n"
        "- Do NOT mention underwriting, risk, points, scores, or insurability.\n"
        "- Do NOT explain severity in financial or insurance terms.\n"
        "- Do NOT infer or add diagnoses.\n"
        "- If information is missing, say it is not available.\n"
        "- Use clear, professional medical language.\n"
        "- 1–3 short paragraphs.\n"
    )

    user = (
        "Summarize the following extracted medical facts:\n\n"
        f"{json.dumps(facts, indent=2)}"
    )

    text = _azure_openai_chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2
    )

    return _paragraphize(text)


# ------------------------------------------------------------------
# 2) UNDERWRITING EXPLANATION (SCORING ONLY)
# ------------------------------------------------------------------

def generate_underwriting_explanation_llm(facts: dict, score_result: dict) -> str:
    compact = {
        "facts": facts,
        "score": score_result.get("score"),
        "breakdown": score_result.get("breakdown", [])
    }

    system = (
        "You are an underwriting analyst.\n"
        "Explain the insurability score based strictly on the provided data.\n\n"
        "STRICT RULES:\n"
        "- Do NOT add medical facts.\n"
        "- Do NOT contradict the score.\n"
        "- Reference score drivers explicitly.\n"
        "- Use underwriting language.\n"
        "- 1–3 short paragraphs.\n"
    )

    user = (
        "Explain the underwriting assessment using this data:\n\n"
        f"{json.dumps(compact, indent=2)}"
    )

    text = _azure_openai_chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2
    )

    return _paragraphize(text)
