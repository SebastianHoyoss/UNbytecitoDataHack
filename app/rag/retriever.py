from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from app.models.schemas import SearchHit
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import LocalVectorStore, PineconeVectorStore


@dataclass
class RetrievalBundle:
    question: str
    hits: list[SearchHit]
    confidence: float
    context: str


@dataclass(frozen=True)
class QueryIntent:
    preferred_categories: set[str]
    preferred_terms: set[str]
    strict: bool = False


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower()


def _tokenize(value: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]{3,}", _normalize(value))
    return set(tokens)


def _detect_intent(question: str) -> QueryIntent:
    q = _normalize(question)

    if any(term in q for term in ("oferta", "pregrado", "posgrado", "tecnologia", "programa", "carrera")):
        return QueryIntent(
            preferred_categories={"oferta_academica", "admisiones"},
            preferred_terms={"programa", "pregrado", "posgrado", "tecnologia", "maestria", "ingenieria", "facultad", "oferta"},
            strict=True,
        )

    if any(term in q for term in ("fecha", "fechas", "cronograma", "calendario", "cuando", "plazo", "vence", "cierre", "inscripcion")):
        return QueryIntent(
            preferred_categories={"fechas_importantes", "inscripciones", "admisiones"},
            preferred_terms={"fecha", "cronograma", "calendario", "inscripcion", "convocatoria", "plazo", "cierre", "apertura"},
            strict=True,
        )

    if any(term in q for term in ("costo", "matricula", "valor", "precio")):
        return QueryIntent(
            preferred_categories={"costos", "admisiones"},
            preferred_terms={"costo", "matricula", "valor", "derechos", "pecuniarios", "precio"},
            strict=False,
        )

    if any(term in q for term in ("requisito", "documento", "admision", "admisiones", "aspirante")):
        return QueryIntent(
            preferred_categories={"requisitos_admision", "admisiones", "inscripciones"},
            preferred_terms={"requisito", "admision", "documento", "aspirante", "inscripcion"},
            strict=False,
        )

    return QueryIntent(preferred_categories=set(), preferred_terms=set(), strict=False)


class Retriever:
    def __init__(self, embeddings: EmbeddingProvider, vector_store: LocalVectorStore | PineconeVectorStore, top_k: int = 5, similarity_threshold: float = 0.24):
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, question: str) -> list[SearchHit]:
        intent = _detect_intent(question)
        query_vector = self.embeddings.embed_query(question)
        candidate_size = max(self.top_k * 6, 20)
        candidates = self.vector_store.query(query_vector, top_k=candidate_size)

        question_terms = _tokenize(question)
        ranked: list[tuple[float, SearchHit]] = []
        for hit in candidates:
            metadata = hit.metadata
            category = str(metadata.get("categoria", "")).lower()
            title = str(metadata.get("titulo", ""))
            url = str(metadata.get("url", ""))
            haystack = f"{title} {url} {hit.text[:1200]}"
            hit_terms = _tokenize(haystack)

            overlap = len(question_terms & hit_terms)
            overlap_score = min(0.24, overlap * 0.04)

            intent_overlap = len(intent.preferred_terms & hit_terms)
            intent_score = min(0.2, intent_overlap * 0.05)

            category_boost = 0.22 if category in intent.preferred_categories else 0.0
            strict_penalty = -0.18 if intent.strict and intent.preferred_categories and category not in intent.preferred_categories else 0.0

            blended_score = float(hit.score) + overlap_score + intent_score + category_boost + strict_penalty
            ranked.append((blended_score, hit))

        ranked.sort(key=lambda item: item[0], reverse=True)

        selected: list[SearchHit] = []
        seen_urls: set[str] = set()
        for _, hit in ranked:
            url = str(hit.metadata.get("url", "")).strip()
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            selected.append(hit)
            if len(selected) >= self.top_k:
                break

        return selected

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