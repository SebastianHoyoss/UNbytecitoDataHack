from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ingestion.processor import load_raw_documents, process_documents, save_processed_chunks


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Procesa documentos crudos de BravoBot")
    parser.add_argument("--input", default=str(settings.raw_dir / "raw_documents.jsonl"))
    parser.add_argument("--output", default=str(settings.processed_dir / "processed_chunks.jsonl"))
    args = parser.parse_args()

    raw_path = Path(args.input)
    output_path = Path(args.output)
    raw_documents = load_raw_documents(raw_path)
    chunks = process_documents(raw_documents, settings)
    save_processed_chunks(chunks, output_path)
    print(f"Documentos crudos: {len(raw_documents)}")
    print(f"Chunks generados: {len(chunks)}")
    print(f"Salida: {output_path}")


if __name__ == "__main__":
    main()