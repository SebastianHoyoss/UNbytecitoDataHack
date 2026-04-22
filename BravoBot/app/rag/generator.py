from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.llm_config import GroqSettings, build_groq_llm
from app.models.schemas import SearchHit

NO_EVIDENCE_MESSAGE = (
    "No encontré información oficial suficiente en las fuentes disponibles de Pascual Bravo para responder con certeza."
)


def load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "core" / "prompts" / "system_prompt.md"
    return prompt_path.read_text(encoding="utf-8")


def build_citations(hits: list[SearchHit]) -> list[str]:
    urls: list[str] = []
    for hit in hits:
        url = str(hit.metadata.get("url", "")).strip()
        if url and url not in urls:
            urls.append(url)
    return urls[:5]


def extractive_answer(question: str, hits: list[SearchHit]) -> str:
    if not hits:
        return NO_EVIDENCE_MESSAGE
    snippets = []
    for hit in hits[:3]:
        text = hit.text.strip()
        if len(text) > 450:
            text = text[:450].rsplit(" ", 1)[0] + "..."
        snippets.append(text)
    citations = "\n".join(f"- {url}" for url in build_citations(hits))
    return (
        "Con base en el contenido oficial recuperado, esto es lo más relevante:\n\n"
        + "\n\n".join(f"- {snippet}" for snippet in snippets)
        + "\n\nFuentes:\n"
        + citations
    )


@dataclass
class GeneratorResult:
    answer: str
    citations: list[str]
    warning: str | None = None


class ResponseGenerator:
    def generate(self, question: str, context: str, hits: list[SearchHit], confidence: float) -> GeneratorResult:
        raise NotImplementedError


class GroqResponseGenerator(ResponseGenerator):
    def __init__(self, settings: GroqSettings):
        self.client = build_groq_llm(settings)
        self.system_prompt = load_system_prompt()

    def generate(self, question: str, context: str, hits: list[SearchHit], confidence: float) -> GeneratorResult:
        citations = build_citations(hits)
        if not context or confidence < 0.24:
            return GeneratorResult(answer=NO_EVIDENCE_MESSAGE, citations=citations, warning="Evidencia insuficiente")

        user_prompt = f"""
Pregunta del aspirante:
{question}

Contexto oficial recuperado:
{context}

Instrucciones:
- Responde en español.
- Usa solo el contexto recuperado.
- No inventes fechas, costos ni requisitos.
- Si hay ambigüedad, acláralo.
- Cierra con una lista corta de URLs usadas en la respuesta.
""".strip()

        completion = self.client.invoke(
            [
                ("system", self.system_prompt),
                ("human", user_prompt),
            ]
        )
        content = getattr(completion, "content", None) or NO_EVIDENCE_MESSAGE
        return GeneratorResult(answer=content.strip(), citations=citations)


class ExtractiveResponseGenerator(ResponseGenerator):
    def generate(self, question: str, context: str, hits: list[SearchHit], confidence: float) -> GeneratorResult:
        citations = build_citations(hits)
        if not hits or confidence < 0.24:
            return GeneratorResult(answer=NO_EVIDENCE_MESSAGE, citations=citations, warning="Evidencia insuficiente")
        return GeneratorResult(answer=extractive_answer(question, hits), citations=citations)