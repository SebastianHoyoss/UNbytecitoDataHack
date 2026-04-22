from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ingestion.indexer import index_processed_chunks


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Indexa documentos procesados en Pinecone o en el almacén local")
    parser.add_argument("--input", default=str(settings.processed_dir / "processed_chunks.jsonl"))
    args = parser.parse_args()

    manifest = index_processed_chunks(settings, Path(args.input))
    print("Indexación completada")
    print(manifest)


if __name__ == "__main__":
    main()