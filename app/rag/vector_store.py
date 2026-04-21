from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.models.schemas import ChunkRecord, SearchHit

logger = logging.getLogger(__name__)


@dataclass
class StoredVector:
    id: str
    embedding: list[float]
    text: str
    metadata: dict[str, object]


class LocalVectorStore:
    def __init__(self, storage_path: Path, namespace: str = "default"):
        self.storage_path = storage_path
        self.namespace = namespace
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._vectors: list[StoredVector] = []
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self._vectors = [StoredVector(**item) for item in payload.get("vectors", [])]
        except Exception:
            logger.warning("No se pudo leer el almacén vectorial local.")

    def _persist(self) -> None:
        payload = {
            "namespace": self.namespace,
            "vectors": [
                {
                    "id": vector.id,
                    "embedding": vector.embedding,
                    "text": vector.text,
                    "metadata": vector.metadata,
                }
                for vector in self._vectors
            ],
        }
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def count(self) -> int:
        return len(self._vectors)

    def upsert(self, chunks: list[ChunkRecord], embeddings: list[list[float]]) -> None:
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            self._vectors = [vector for vector in self._vectors if vector.id != chunk.id]
            self._vectors.append(
                StoredVector(
                    id=chunk.id,
                    embedding=list(map(float, embedding)),
                    text=chunk.text,
                    metadata={
                        **chunk.metadata.model_dump(mode="json"),
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "token_count": chunk.token_count,
                    },
                )
            )
        self._persist()

    def query(self, vector: list[float], top_k: int = 5) -> list[SearchHit]:
        if not self._vectors:
            return []

        query = np.asarray(vector, dtype=float)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        scored: list[tuple[float, StoredVector]] = []
        for stored_vector in self._vectors:
            candidate = np.asarray(stored_vector.embedding, dtype=float)
            denom = np.linalg.norm(candidate) * query_norm
            score = float(np.dot(query, candidate) / denom) if denom else 0.0
            scored.append((score, stored_vector))

        scored.sort(key=lambda item: item[0], reverse=True)
        hits: list[SearchHit] = []
        for score, stored_vector in scored[:top_k]:
            hits.append(
                SearchHit(
                    id=stored_vector.id,
                    score=score,
                    text=stored_vector.text,
                    metadata=stored_vector.metadata,
                )
            )
        return hits


class PineconeVectorStore:
    def __init__(self, api_key: str, index_name: str, namespace: str, dimension: int, cloud: str = "aws", region: str = "us-east-1"):
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError as exc:
            raise RuntimeError("Falta instalar pinecone. Revisa requirements.txt.") from exc

        self._client = Pinecone(api_key=api_key)
        self._serverless_spec = ServerlessSpec(cloud=cloud, region=region)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self._ensure_index()
        self._index = self._client.Index(index_name)

    def _ensure_index(self) -> None:
        existing_indexes = []
        try:
            existing = self._client.list_indexes()
            existing_indexes = existing.names() if hasattr(existing, "names") else [item["name"] for item in existing]
        except Exception:
            existing_indexes = []
        if self.index_name not in existing_indexes:
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=self._serverless_spec,
            )

    def count(self) -> int:
        try:
            stats = self._index.describe_index_stats()
            namespaces = getattr(stats, "namespaces", {}) or {}
            namespace_stats = namespaces.get(self.namespace, {})
            return int(namespace_stats.get("vector_count", 0))
        except Exception:
            return 0

    def upsert(self, chunks: list[ChunkRecord], embeddings: list[list[float]]) -> None:
        records = []
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            metadata = {
                **chunk.metadata.model_dump(mode="json"),
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "_document": chunk.text,
            }
            clean_metadata: dict[str, object] = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    clean_metadata[key] = value
                else:
                    clean_metadata[key] = str(value)
            records.append(
                (
                    chunk.id,
                    list(map(float, embedding)),
                    clean_metadata,
                )
            )
        self._index.upsert(vectors=records, namespace=self.namespace)

    def query(self, vector: list[float], top_k: int = 5) -> list[SearchHit]:
        response = self._index.query(vector=vector, top_k=top_k, namespace=self.namespace, include_metadata=True)
        matches = getattr(response, "matches", []) or []
        hits: list[SearchHit] = []
        for match in matches:
            metadata = dict(getattr(match, "metadata", {}) or {})
            text = str(metadata.pop("_document", metadata.pop("text", "")))
            hits.append(
                SearchHit(
                    id=getattr(match, "id", ""),
                    score=float(getattr(match, "score", 0.0)),
                    text=text,
                    metadata=metadata,
                )
            )
        return hits


def build_vector_store(settings, dimension: int) -> LocalVectorStore | PineconeVectorStore:
    if settings.pinecone_api_key:
        return PineconeVectorStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            namespace=settings.pinecone_namespace,
            dimension=dimension,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        )
    if not settings.allow_local_vectorstore:
        raise RuntimeError(
            "Falta configurar PINECONE_API_KEY y el modo local está deshabilitado."
        )
    return LocalVectorStore(storage_path=settings.processed_dir / "local_vector_store.json", namespace=settings.pinecone_namespace)