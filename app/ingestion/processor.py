from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings
from app.models.schemas import ChunkRecord, RawDocument
from app.utils.text import chunk_text, clean_text, infer_category


def load_raw_documents(raw_path: Path) -> list[RawDocument]:
    documents: list[RawDocument] = []
    if not raw_path.exists():
        return documents
    with raw_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            documents.append(RawDocument.model_validate_json(line))
    return documents


def process_documents(documents: list[RawDocument], settings: Settings) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    for document in documents:
        clean_source = clean_text(document.text)
        category = infer_category(document.url, document.titulo)
        for chunk_index, chunk in enumerate(
            chunk_text(
                clean_source,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        ):
            chunks.append(
                ChunkRecord(
                    id=f"{document.document_id}-{chunk_index}",
                    document_id=document.document_id,
                    text=chunk,
                    chunk_index=chunk_index,
                    metadata={
                        "url": document.url,
                        "titulo": document.titulo,
                        "fecha_scrapeo": document.fecha_scrapeo,
                        "categoria": category,
                        "idioma": document.idioma,
                        "hash": document.hash,
                    },
                    token_count=len(chunk.split()),
                )
            )
    return chunks


def save_processed_chunks(chunks: list[ChunkRecord], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(chunk.model_dump_json())
            handle.write("\n")
    return output_path


def build_processed_manifest(chunks: list[ChunkRecord]) -> dict[str, object]:
    categories = sorted({chunk.metadata.categoria for chunk in chunks})
    urls = [chunk.metadata.url for chunk in chunks]
    latest_sources = []
    seen = set()
    for url in reversed(urls):
        if url not in seen:
            latest_sources.append(url)
            seen.add(url)
        if len(latest_sources) == 10:
            break
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "documents_indexed": len({chunk.document_id for chunk in chunks}),
        "chunks_indexed": len(chunks),
        "category_counts": {
            category: sum(1 for chunk in chunks if chunk.metadata.categoria == category)
            for category in categories
        },
        "latest_sources": latest_sources,
        "categories": categories,
    }


def save_processed_manifest(manifest: dict[str, object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path