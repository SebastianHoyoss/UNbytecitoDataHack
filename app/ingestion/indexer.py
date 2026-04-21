from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.ingestion.processor import build_processed_manifest, save_processed_manifest
from app.models.schemas import ChunkRecord
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import build_vector_store


def load_processed_chunks(processed_path: Path) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    if not processed_path.exists():
        return chunks
    with processed_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            chunks.append(ChunkRecord.model_validate_json(line))
    return chunks


def index_processed_chunks(settings: Settings, processed_path: Path) -> dict[str, object]:
    chunks = load_processed_chunks(processed_path)
    if not chunks:
        raise RuntimeError(
            f"No se encontraron chunks procesados en {processed_path}. Ejecuta primero python -m scripts.process."
        )

    embedder = build_embedding_provider(settings.embedding_model)
    store = build_vector_store(settings, embedder.dimension)

    batch_size = 32
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        embeddings = embedder.embed_texts([chunk.text for chunk in batch])
        store.upsert(batch, embeddings)

    manifest = build_processed_manifest(chunks)
    manifest_path = settings.processed_dir / settings.processed_manifest_name
    save_processed_manifest(manifest, manifest_path)
    return manifest