from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bs4 import BeautifulSoup
from requests import Session
from trafilatura import extract as trafilatura_extract

from app.core.config import Settings
from app.models.schemas import DocumentMetadata, RawDocument
from app.utils.http import canonicalize_url, detect_language, fetch_url, parse_html_title, robots_allowed
from app.utils.text import clean_text, hash_text, infer_category

logger = logging.getLogger(__name__)


def _fallback_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text("\n", strip=True)
    return clean_text(text)


def extract_main_text(html: str) -> str:
    try:
        extracted = trafilatura_extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
    except Exception:
        extracted = None
    text = extracted.strip() if extracted else _fallback_text(html)
    return clean_text(text)


@dataclass
class ScrapeResult:
    documents: list[RawDocument]
    skipped_urls: list[str]


class SiteScraper:
    def __init__(self, settings: Settings, session: Session):
        self.settings = settings
        self.session = session

    def scrape_url(self, url: str) -> RawDocument | None:
        url = canonicalize_url(url)
        if not robots_allowed(url, self.settings.user_agent):
            logger.info("Bloqueado por robots.txt: %s", url)
            return None

        try:
            response = fetch_url(url, self.session, delay_seconds=self.settings.scrape_delay_seconds)
        except Exception as exc:
            logger.warning("No se pudo obtener %s: %s", url, exc)
            return None

        html = response.text
        text = extract_main_text(html)
        if not text:
            return None

        title = parse_html_title(html)
        language = detect_language(html)
        scraped_at = datetime.now(tz=UTC)
        content_hash = hash_text(text)
        document_id = content_hash[:16]

        metadata = DocumentMetadata(
            url=url,
            titulo=title,
            fecha_scrapeo=scraped_at,
            categoria=infer_category(url, title),
            idioma=language,
            hash=content_hash,
        )
        return RawDocument(
            document_id=document_id,
            url=url,
            titulo=title,
            text=text,
            html=html,
            fecha_scrapeo=scraped_at,
            categoria=metadata.categoria,
            idioma=language,
            hash=content_hash,
        )

    def scrape_urls(self, urls: list[str]) -> ScrapeResult:
        documents: list[RawDocument] = []
        skipped: list[str] = []
        seen_hashes: set[str] = set()
        for url in urls:
            document = self.scrape_url(url)
            if document is None:
                skipped.append(url)
                continue
            if document.hash in seen_hashes:
                continue
            seen_hashes.add(document.hash)
            documents.append(document)
        return ScrapeResult(documents=documents, skipped_urls=skipped)

    def save_raw_documents(self, documents: list[RawDocument], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for document in documents:
                handle.write(document.model_dump_json())
                handle.write("\n")
        return output_path

    def save_manifest(self, discovered_urls: list[str], documents: list[RawDocument], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "scraped_at": datetime.now(tz=UTC).isoformat(),
            "discovered_urls": len(discovered_urls),
            "documents_saved": len(documents),
            "sources": [document.url for document in documents[:20]],
            "categories": sorted({document.categoria for document in documents}),
        }
        output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path