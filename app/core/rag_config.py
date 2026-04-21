from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.core.config import hydrate_env_from_streamlit_secrets


def _normalize_embedding_model(model_name: str) -> str:
    model_name = model_name.strip()
    if "/" not in model_name:
        return f"sentence-transformers/{model_name}"
    return model_name


@dataclass(frozen=True)
class RagSettings:
    embedding_model: str = "all-MiniLM-L6-v2"
    pinecone_api_key: str = ""
    pinecone_index: str = "bravobot-index"
    pinecone_namespace: str = "bravobot"
    top_k: int = 5

    @classmethod
    def from_env(cls) -> "RagSettings":
        repo_root = Path(__file__).resolve().parents[2]
        load_dotenv(repo_root / ".env", override=False)
        hydrate_env_from_streamlit_secrets(
            (
                "PINECONE_API_KEY",
                "PINECONE_INDEX",
                "PINECONE_INDEX_NAME",
                "PINECONE_NAMESPACE",
                "RAG_EMBEDDING_MODEL",
                "RAG_TOP_K",
            )
        )

        index_name = os.getenv("PINECONE_INDEX", "").strip() or os.getenv("PINECONE_INDEX_NAME", "bravobot-index").strip()
        return cls(
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip(),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", "").strip(),
            pinecone_index=index_name,
            pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "bravobot").strip(),
            top_k=int(os.getenv("RAG_TOP_K", "5")),
        )


def build_embedding_model(settings: RagSettings | None = None):
    cfg = settings or RagSettings.from_env()
    model_name = _normalize_embedding_model(cfg.embedding_model)
    return _cached_embedding_model(model_name)


@lru_cache(maxsize=4)
def _cached_embedding_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Falta instalar sentence-transformers. Revisa requirements.txt.") from exc

    return SentenceTransformer(model_name)


def _build_pinecone_index(settings: RagSettings | None = None):
    cfg = settings or RagSettings.from_env()
    if not cfg.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY no configurada en .env")

    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise RuntimeError("Falta instalar pinecone. Revisa requirements.txt.") from exc

    client = Pinecone(api_key=cfg.pinecone_api_key)
    return client.Index(cfg.pinecone_index)


def upsert_rag_documents(
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
    ids: list[str] | None = None,
    settings: RagSettings | None = None,
) -> int:
    if not documents:
        return 0

    cfg = settings or RagSettings.from_env()
    index = _build_pinecone_index(cfg)
    model = build_embedding_model(cfg)

    final_ids = ids or [str(uuid.uuid4()) for _ in documents]
    embeddings = model.encode(documents).tolist()

    vectors: list[dict[str, Any]] = []
    for i, (vector_id, embedding, document) in enumerate(zip(final_ids, embeddings, documents, strict=False)):
        metadata = dict(metadatas[i]) if metadatas and i < len(metadatas) else {}
        metadata["_document"] = str(document)[:39000]

        clean_metadata: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                clean_metadata[key] = value
            else:
                clean_metadata[key] = str(value)

        vectors.append({"id": vector_id, "values": embedding, "metadata": clean_metadata})

    batch_size = 100
    for start in range(0, len(vectors), batch_size):
        batch = vectors[start : start + batch_size]
        index.upsert(vectors=batch, namespace=cfg.pinecone_namespace)

    return len(documents)


def retrieve_rag_context(
    query_text: str,
    settings: RagSettings | None = None,
    n_results: int | None = None,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cfg = settings or RagSettings.from_env()
    index = _build_pinecone_index(cfg)
    model = build_embedding_model(cfg)

    top_k = n_results or cfg.top_k
    query_embedding = model.encode([query_text]).tolist()[0]

    query_kwargs: dict[str, Any] = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
        "namespace": cfg.pinecone_namespace,
    }

    if where:
        pinecone_filter: dict[str, Any] = {}
        for key, value in where.items():
            pinecone_filter[key] = value if isinstance(value, dict) else {"$eq": value}
        query_kwargs["filter"] = pinecone_filter

    response = index.query(**query_kwargs)
    matches = []
    if hasattr(response, "matches"):
        matches = list(getattr(response, "matches", []) or [])
    elif isinstance(response, dict):
        matches = list(response.get("matches", []) or [])

    items: list[dict[str, Any]] = []
    for match in matches:
        metadata = dict(getattr(match, "metadata", None) or (match.get("metadata", {}) if isinstance(match, dict) else {}))
        score = float(getattr(match, "score", None) or (match.get("score", 0.0) if isinstance(match, dict) else 0.0))
        document = str(metadata.pop("_document", ""))
        items.append(
            {
                "document": document,
                "metadata": metadata,
                "distance": 1.0 - score,
            }
        )
    return items
