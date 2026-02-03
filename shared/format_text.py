import os
import json
import requests


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise ValueError(f"Missing env var: {name}")
    return v


def _azure_openai_chat(messages, temperature=0.2, max_tokens=450) -> str:
    """
    Calls Azure OpenAI Chat Completions (works for most deployments).
    Env vars expected:
      OPENAI_ENDPOINT      e.g. https://<resource-name>.openai.azure.com
      OPENAI_API_KEY
      OPENAI_DEPLOYMENT    e.g. gpt-4.1-mini (your deployment name)
      OPENAI_API_VERSION   optional; default 2024-02-15-preview
    """
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
    data = r.json()
    return data["choices"][0]["message"]["content"]


def format_underwriting_text_llm(facts: dict, score_result: dict) -> str:
    """
    Generates a human-readable underwriting narrative using the LLM,
    but ONLY from extracted facts + score (no raw OCR text).
    """

    # Minimize + stabilize the input
    compact = {
        "facts": facts,
        "score": score_result.get("score"),
        "breakdown": score_result.get("breakdown", [])
    }

    system = (
        "You are an underwriting assistant writing a concise narrative summary.\n"
        "Rules:\n"
        "1) Use ONLY the provided JSON. Do NOT add new facts.\n"
        "2) Do NOT change the score.\n"
        "3) If a field is null/unknown, say it is not available (do not guess).\n"
        "4) Keep it professional, 6-12 sentences max.\n"
        "5) Focus on the main drivers (stroke/TIA, DKA, retinopathy, CKD, CAD/MI, med burden, etc.)."
    )

    user = (
        "Write an underwriting narrative based ONLY on this JSON:\n\n"
        f"{json.dumps(compact, indent=2)}"
    )

    text = _azure_openai_chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2,
        max_tokens=450
    )

    return text.strip()
