import os
import json
import requests
import re


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise ValueError(f"Missing env var: {name}")
    return v


def _azure_openai_chat(messages, temperature=0.2, max_tokens=450) -> str:
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


def _paragraphize(text: str, sentences_per_paragraph: int = 2) -> str:
    """
    Converts a long single-line LLM response into readable paragraphs.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Split into sentences conservatively
    sentences = re.split(r"(?<=[.!?])\s+", text)

    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        chunk = sentences[i:i + sentences_per_paragraph]
        paragraphs.append(" ".join(chunk))

    return "\n\n".join(paragraphs)


def format_underwriting_text_llm(facts: dict, score_result: dict) -> str:
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
        "3) If a field is null/unknown, state it is not available.\n"
        "4) Keep it professional and clear.\n"
        "5) Focus on the primary underwriting drivers.\n"
        "6) Write in complete sentences."
    )

    user = (
        "Write an underwriting narrative based ONLY on this JSON:\n\n"
        f"{json.dumps(compact, indent=2)}"
    )

    raw_text = _azure_openai_chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2,
        max_tokens=450
    )

    return _paragraphize(raw_text)
