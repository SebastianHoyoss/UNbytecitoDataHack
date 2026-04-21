from __future__ import annotations

from pathlib import Path
import logging

from app.core.config import Settings
from app.core.rag_config import RagSettings, upsert_rag_documents
from app.ingestion.processor import build_processed_manifest, save_processed_manifest
from app.models.schemas import ChunkRecord
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import LocalVectorStore


logger = logging.getLogger(__name__)


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

    indexed_in_pinecone = False
    if settings.pinecone_api_key:
        rag_settings = RagSettings(
            embedding_model=settings.embedding_model,
            pinecone_api_key=settings.pinecone_api_key,
            pinecone_index=settings.pinecone_index_name,
            pinecone_namespace=settings.pinecone_namespace,
            top_k=settings.top_k,
        )
        documents = [chunk.text for chunk in chunks]
        ids = [chunk.id for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadatas.append(
                {
                    **chunk.metadata.model_dump(mode="json"),
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                }
            )
        try:
            upsert_rag_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                settings=rag_settings,
            )
            indexed_in_pinecone = True
        except Exception as exc:
            if not settings.allow_local_vectorstore:
                raise
            logger.warning(
                "No fue posible indexar en Pinecone (%s). Se usara vector store local.",
                exc,
            )

    if not indexed_in_pinecone:
        embedder = build_embedding_provider(settings.embedding_model)
        store = LocalVectorStore(
            storage_path=settings.processed_dir / "local_vector_store.json",
            namespace=settings.pinecone_namespace,
        )

        batch_size = 32
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = embedder.embed_texts([chunk.text for chunk in batch])
            store.upsert(batch, embeddings)

    manifest = build_processed_manifest(chunks)
    manifest_path = settings.processed_dir / settings.processed_manifest_name
    save_processed_manifest(manifest, manifest_path)
    return manifest