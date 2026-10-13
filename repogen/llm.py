import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()


def generate_text(system: str, prompt: str, max_tokens: int = 400) -> str:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is not set. Add it to .env or your host's secrets.")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

    client = InferenceClient(api_key=token)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
