import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def generate_text(system: str, prompt: str, max_tokens: int = 400) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env or your host's secrets.")
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    client = Groq(api_key=key)
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
