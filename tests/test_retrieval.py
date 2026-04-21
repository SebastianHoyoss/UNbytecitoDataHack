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