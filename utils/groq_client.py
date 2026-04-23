import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_keys = [k for k in [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY_2"),
] if k]

_current = 0


def chat(model: str, messages: list) -> str:
    global _current
    last_error = None

    for attempt in range(len(_keys)):
        key_index = (_current + attempt) % len(_keys)
        try:
            client = Groq(api_key=_keys[key_index])
            response = client.chat.completions.create(model=model, messages=messages)
            _current = key_index
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < len(_keys) - 1:
                last_error = e
                continue
            raise

    raise last_error
