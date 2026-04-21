from pathlib import Path

from app.models.schemas import ChunkRecord, DocumentMetadata
from app.rag.retriever import Retriever
from app.rag.vector_store import LocalVectorStore


class DummyEmbedder:
    dimension = 2

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        lower = text.lower()
        if "inscrip" in lower:
            return [1.0, 0.0]
        if "costo" in lower:
            return [0.0, 1.0]
        return [0.5, 0.5]


class FlatEmbedder:
    dimension = 2

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 1.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 1.0]


def test_retriever_returns_relevant_hit(tmp_path: Path) -> None:
    store = LocalVectorStore(storage_path=tmp_path / "vectors.json")
    embedder = DummyEmbedder()

    chunk = ChunkRecord(
        id="doc-1-0",
        document_id="doc-1",
        text="Información sobre inscripciones y requisitos de admisión.",
        chunk_index=0,
        metadata=DocumentMetadata(
            url="https://pascualbravo.edu.co/admisiones",
            titulo="Admisiones",
            fecha_scrapeo="2026-04-21T00:00:00Z",
            categoria="admisiones",
            idioma="es",
            hash="abc123",
        ),
        token_count=8,
    )
    store.upsert([chunk], embedder.embed_texts([chunk.text]))
    retriever = Retriever(embedder, store, top_k=1)

    hits = retriever.retrieve("¿Cuándo abren inscripciones?")
    assert len(hits) == 1
    assert hits[0].metadata["categoria"] == "admisiones"


def test_retriever_prioritizes_academic_offer_intent(tmp_path: Path) -> None:
    store = LocalVectorStore(storage_path=tmp_path / "vectors_offer.json")
    embedder = FlatEmbedder()

    offer_chunk = ChunkRecord(
        id="doc-offer-0",
        document_id="doc-offer",
        text="Programas de pregrado, posgrado y tecnologia en las facultades del Pascual Bravo.",
        chunk_index=0,
        metadata=DocumentMetadata(
            url="https://pascualbravo.edu.co/facultades/facultad-de-ingenieria/programas",
            titulo="Oferta academica",
            fecha_scrapeo="2026-04-21T00:00:00Z",
            categoria="oferta_academica",
            idioma="es",
            hash="offer",
        ),
        token_count=12,
    )
    wellness_chunk = ChunkRecord(
        id="doc-wellness-0",
        document_id="doc-wellness",
        text="Actividades de bienestar universitario, cultura y deporte para estudiantes.",
        chunk_index=0,
        metadata=DocumentMetadata(
            url="https://pascualbravo.edu.co/academico/bienestar-universitario/servicios/cultura",
            titulo="Cultura",
            fecha_scrapeo="2026-04-21T00:00:00Z",
            categoria="general",
            idioma="es",
            hash="wellness",
        ),
        token_count=10,
    )

    chunks = [offer_chunk, wellness_chunk]
    store.upsert(chunks, embedder.embed_texts([chunk.text for chunk in chunks]))
    retriever = Retriever(embedder, store, top_k=1)

    hits = retriever.retrieve("Cual es la oferta academica del Pascual Bravo?")
    assert len(hits) == 1
    assert hits[0].metadata["categoria"] == "oferta_academica"


def test_retriever_prioritizes_dates_intent(tmp_path: Path) -> None:
    store = LocalVectorStore(storage_path=tmp_path / "vectors_dates.json")
    embedder = FlatEmbedder()

    dates_chunk = ChunkRecord(
        id="doc-dates-0",
        document_id="doc-dates",
        text="Cronograma de inscripciones con fechas de apertura y cierre para aspirantes.",
        chunk_index=0,
        metadata=DocumentMetadata(
            url="https://pascualbravo.edu.co/academico/programa-de-ingles/cronograma",
            titulo="Cronograma",
            fecha_scrapeo="2026-04-21T00:00:00Z",
            categoria="fechas_importantes",
            idioma="es",
            hash="dates",
        ),
        token_count=12,
    )
    generic_chunk = ChunkRecord(
        id="doc-generic-0",
        document_id="doc-generic",
        text="Informacion institucional general sobre identidad y servicios.",
        chunk_index=0,
        metadata=DocumentMetadata(
            url="https://pascualbravo.edu.co/acerca-del-pascual/identidad-institucional",
            titulo="Identidad institucional",
            fecha_scrapeo="2026-04-21T00:00:00Z",
            categoria="general",
            idioma="es",
            hash="generic",
        ),
        token_count=8,
    )

    chunks = [dates_chunk, generic_chunk]
    store.upsert(chunks, embedder.embed_texts([chunk.text for chunk in chunks]))
    retriever = Retriever(embedder, store, top_k=1)

    hits = retriever.retrieve("Que fechas importantes se aproximan para inscripciones?")
    assert len(hits) == 1
    assert hits[0].metadata["categoria"] == "fechas_importantes"