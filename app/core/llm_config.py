from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.core.config import hydrate_env_from_streamlit_secrets


@dataclass(frozen=True)
class GroqSettings:
    api_key: str
    model_name: str = "openai/gpt-oss-120b"
    temperature: float = 0.1
    max_tokens: int = 700
    request_timeout: float = 60.0
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "GroqSettings":
        repo_root = Path(__file__).resolve().parents[2]
        load_dotenv(repo_root / ".env", override=False)
        hydrate_env_from_streamlit_secrets(
            (
                "GROQ_API_KEY",
                "GROQ_MODEL",
                "GROQ_TEMPERATURE",
                "GROQ_MAX_TOKENS",
                "GROQ_REQUEST_TIMEOUT",
                "GROQ_MAX_RETRIES",
            )
        )

        return cls(
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
            model_name=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip(),
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "700")),
            request_timeout=float(os.getenv("GROQ_REQUEST_TIMEOUT", "60")),
            max_retries=int(os.getenv("GROQ_MAX_RETRIES", "2")),
        )


def build_groq_llm(settings: GroqSettings | None = None):
    cfg = settings or GroqSettings.from_env()
    if not cfg.api_key:
        raise ValueError("GROQ_API_KEY no está configurada.")

    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise RuntimeError("Falta instalar langchain-groq. Revisa requirements.txt.") from exc

    return ChatGroq(
        model_name=cfg.model_name,
        groq_api_key=cfg.api_key,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        request_timeout=cfg.request_timeout,
        max_retries=cfg.max_retries,
    )
