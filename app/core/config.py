from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


STREAMLIT_SECRET_KEYS: tuple[str, ...] = (
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "GROQ_TEMPERATURE",
    "GROQ_MAX_TOKENS",
    "GROQ_REQUEST_TIMEOUT",
    "GROQ_MAX_RETRIES",
    "PINECONE_API_KEY",
    "PINECONE_INDEX",
    "PINECONE_INDEX_NAME",
    "PINECONE_NAMESPACE",
    "RAG_EMBEDDING_MODEL",
    "RAG_TOP_K",
)


def hydrate_env_from_streamlit_secrets(keys: tuple[str, ...] = STREAMLIT_SECRET_KEYS) -> None:
    try:
        import streamlit as st

        for key in keys:
            if not os.environ.get(key):
                value = st.secrets.get(key)
                if value is not None:
                    os.environ[key] = str(value)
    except Exception:
        # Streamlit no siempre está disponible en contexto API/CLI.
        return


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="BravoBot", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    base_url: str = Field(default="https://pascualbravo.edu.co/", alias="BASE_URL")
    user_agent: str = Field(
        default="BravoBot/0.1 (+https://pascualbravo.edu.co/; contact: dev@bravobot.local)",
        alias="USER_AGENT",
    )
    scrape_delay_seconds: float = Field(default=1.0, alias="SCRAPE_DELAY_SECONDS")
    max_pages: int = Field(default=120, alias="MAX_PAGES")
    chunk_size: int = Field(default=1200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=180, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=5, validation_alias=AliasChoices("TOP_K", "RAG_TOP_K"))
    similarity_threshold: float = Field(default=0.24, alias="SIMILARITY_THRESHOLD")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        validation_alias=AliasChoices("EMBEDDING_MODEL", "RAG_EMBEDDING_MODEL"),
    )
    llm_model: str = Field(default="openai/gpt-oss-120b", validation_alias=AliasChoices("LLM_MODEL", "GROQ_MODEL"))
    groq_temperature: float = Field(default=0.1, alias="GROQ_TEMPERATURE")
    groq_max_tokens: int = Field(default=700, alias="GROQ_MAX_TOKENS")
    groq_request_timeout: float = Field(default=60.0, alias="GROQ_REQUEST_TIMEOUT")
    groq_max_retries: int = Field(default=2, alias="GROQ_MAX_RETRIES")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    pinecone_api_key: str | None = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_environment: str | None = Field(default=None, alias="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="bravobot-index", validation_alias=AliasChoices("PINECONE_INDEX_NAME", "PINECONE_INDEX"))
    pinecone_namespace: str = Field(default="bravobot", alias="PINECONE_NAMESPACE")
    pinecone_cloud: str = Field(default="aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_REGION")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    allow_local_vectorstore: bool = Field(default=True, alias="ALLOW_LOCAL_VECTORSTORE")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    raw_dir: Path = Field(default=Path("data/raw"), alias="RAW_DIR")
    processed_dir: Path = Field(default=Path("data/processed"), alias="PROCESSED_DIR")
    logs_dir: Path = Field(default=Path("logs"), alias="LOGS_DIR")
    raw_manifest_name: str = Field(default="raw_manifest.json", alias="RAW_MANIFEST_NAME")
    processed_manifest_name: str = Field(default="index_manifest.json", alias="PROCESSED_MANIFEST_NAME")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        valid_values = {"local", "development", "staging", "production"}
        if value not in valid_values:
            raise ValueError(f"APP_ENV debe ser uno de: {', '.join(sorted(valid_values))}")
        return value

    @field_validator("embedding_model")
    @classmethod
    def normalize_embedding_model(cls, value: str) -> str:
        # Compatibilidad con formato corto recomendado en EJEMPLO.
        if "/" not in value:
            return f"sentence-transformers/{value}"
        return value

    def ensure_directories(self) -> None:
        for directory in (self.data_dir, self.raw_dir, self.processed_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    hydrate_env_from_streamlit_secrets()
    settings = Settings()
    settings.ensure_directories()
    return settings