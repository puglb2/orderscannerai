import base64
import os
from openai import AzureOpenAI


def get_openai_client():
    return AzureOpenAI(
        api_key=os.getenv("OPENAI_KEY"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )


def detect_signature_from_image(image_base64: str) -> bool:

    client = get_openai_client()
    deployment = os.getenv("OPENAI_DEPLOYMENT")

    prompt = """
Does this medical document page contain a handwritten or drawn signature?

Respond ONLY with JSON:

{
  "signature_present": true or false
}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    return "true" in result.lower()
