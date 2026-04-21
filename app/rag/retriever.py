from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import SearchHit
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import LocalVectorStore, PineconeVectorStore


@dataclass
class RetrievalBundle:
    question: str
    hits: list[SearchHit]
    confidence: float
    context: str


class Retriever:
    def __init__(self, embeddings: EmbeddingProvider, vector_store: LocalVectorStore | PineconeVectorStore, top_k: int = 5, similarity_threshold: float = 0.24):
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, question: str) -> list[SearchHit]:
        query_vector = self.embeddings.embed_query(question)
        return self.vector_store.query(query_vector, top_k=self.top_k)

    def build_bundle(self, question: str) -> RetrievalBundle:
        hits = self.retrieve(question)
        confidence = max((hit.score for hit in hits), default=0.0)
        context_parts: list[str] = []
        for hit in hits:
            metadata = hit.metadata
            url = metadata.get("url", "")
            title = metadata.get("titulo", "")
            context_parts.append(
                f"FUENTE: {url}\nTITULO: {title}\nCONTENIDO: {hit.text[:1800]}"
            )
        return RetrievalBundle(
            question=question,
            hits=hits,
            confidence=confidence,
            context="\n\n".join(context_parts),
        )