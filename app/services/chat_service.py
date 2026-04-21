from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.models.schemas import ChatResponse, SourceReference
from app.rag.embeddings import build_embedding_provider
from app.rag.generator import ExtractiveResponseGenerator, GroqResponseGenerator, NO_EVIDENCE_MESSAGE
from app.rag.retriever import Retriever
from app.rag.vector_store import build_vector_store


@dataclass
class ChatService:
    settings: Settings
    retriever: Retriever
    generator: object
    vector_store_name: str

    def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
        session_id = session_id or str(uuid4())
        bundle = self.retriever.build_bundle(question)
        hits = [hit for hit in bundle.hits if hit.score >= self.retriever.similarity_threshold]
        confidence = max((hit.score for hit in hits), default=bundle.confidence)

        if not hits:
            return ChatResponse(
                answer=NO_EVIDENCE_MESSAGE,
                sources=[],
                confidence=0.0,
                session_id=session_id,
                answer_mode="fallback",
                warning="No se recuperó suficiente evidencia oficial.",
            )

        generator_result = self.generator.generate(question, bundle.context, hits, confidence)
        sources = [
            SourceReference(
                url=str(hit.metadata.get("url", "")),
                titulo=str(hit.metadata.get("titulo", "")) or None,
                score=hit.score,
            )
            for hit in hits[:5]
            if hit.metadata.get("url")
        ]
        answer_mode = "llm" if isinstance(self.generator, GroqResponseGenerator) else "extractive"
        if generator_result.warning:
            answer_mode = "fallback"

        return ChatResponse(
            answer=generator_result.answer,
            sources=sources,
            confidence=confidence,
            session_id=session_id,
            answer_mode=answer_mode,
            warning=generator_result.warning,
        )


def build_chat_service(settings: Settings | None = None) -> ChatService:
    settings = settings or get_settings()
    embeddings = build_embedding_provider(settings.embedding_model)
    vector_store = build_vector_store(settings, embeddings.dimension)
    retriever = Retriever(
        embeddings=embeddings,
        vector_store=vector_store,
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
    )
    if settings.groq_api_key:
        generator = GroqResponseGenerator(api_key=settings.groq_api_key, model=settings.llm_model)
    else:
        generator = ExtractiveResponseGenerator()
    return ChatService(
        settings=settings,
        retriever=retriever,
        generator=generator,
        vector_store_name=vector_store.__class__.__name__,
    )