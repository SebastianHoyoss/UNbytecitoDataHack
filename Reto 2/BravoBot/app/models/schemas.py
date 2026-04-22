from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    url: str
    titulo: str = ""
    fecha_scrapeo: datetime
    categoria: str = "general"
    idioma: str = "es"
    hash: str


class RawDocument(BaseModel):
    document_id: str
    url: str
    titulo: str = ""
    text: str
    html: str | None = None
    fecha_scrapeo: datetime
    categoria: str = "general"
    idioma: str = "es"
    hash: str


class ChunkRecord(BaseModel):
    id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: DocumentMetadata
    token_count: int = 0


class SearchHit(BaseModel):
    id: str
    score: float
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceReference(BaseModel):
    url: str
    titulo: str | None = None
    score: float | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, max_length=128)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("La pregunta no puede estar vacía")
        return cleaned


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    confidence: float = 0.0
    session_id: str
    answer_mode: str
    warning: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    vector_store: str
    llm_configured: bool
    documents_indexed: int = 0