from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ingestion.discovery import discover_relevant_urls
from app.ingestion.scraper import SiteScraper
from app.utils.http import build_session


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Scraper oficial de BravoBot")
    parser.add_argument("--base-url", default=settings.base_url)
    parser.add_argument("--max-pages", type=int, default=settings.max_pages)
    parser.add_argument("--output", default=str(settings.raw_dir / "raw_documents.jsonl"))
    args = parser.parse_args()

    session = build_session(settings.user_agent)
    scraper = SiteScraper(settings=settings, session=session)
    discovered = discover_relevant_urls(
        base_url=args.base_url,
        session=session,
        user_agent=settings.user_agent,
        max_pages=args.max_pages,
    )
    result = scraper.scrape_urls([item.url for item in discovered])
    output_path = Path(args.output)
    scraper.save_raw_documents(result.documents, output_path)
    scraper.save_manifest([item.url for item in discovered], result.documents, settings.raw_dir / settings.raw_manifest_name)
    print(f"URLs descubiertas: {len(discovered)}")
    print(f"Documentos guardados: {len(result.documents)}")
    print(f"Salida: {output_path}")


if __name__ == "__main__":
    main()