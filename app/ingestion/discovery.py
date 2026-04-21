from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

from requests import Session

from app.utils.http import canonicalize_url, extract_internal_links, fetch_url, robots_allowed
from app.utils.text import infer_category, unique_preserve_order

logger = logging.getLogger(__name__)

RELEVANT_KEYWORDS = (
    "admis",
    "inscrip",
    "costo",
    "matric",
    "pregrado",
    "posgrado",
    "tecnolog",
    "programa",
    "oferta",
    "requisit",
    "aspirant",
)


@dataclass(frozen=True)
class DiscoveredUrl:
    url: str
    categoria: str


def _keyword_match(url: str) -> bool:
    haystack = url.lower()
    return any(keyword in haystack for keyword in RELEVANT_KEYWORDS)


def _parse_sitemap_urls(xml_payload: str) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_payload)
    except ET.ParseError:
        return urls

    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    for loc in root.findall(f".//{namespace}loc"):
        if loc.text:
            urls.append(canonicalize_url(loc.text.strip()))
    return urls


def discover_relevant_urls(
    base_url: str,
    session: Session,
    user_agent: str,
    max_pages: int = 120,
) -> list[DiscoveredUrl]:
    base_url = canonicalize_url(base_url)
    discovered: list[str] = []
    seen: set[str] = set()
    queue: deque[str] = deque([base_url])

    sitemap_url = urljoin(base_url + "/", "sitemap.xml")
    if robots_allowed(sitemap_url, user_agent):
        try:
            sitemap_response = fetch_url(sitemap_url, session, delay_seconds=0)
            sitemap_urls = _parse_sitemap_urls(sitemap_response.text)
            for sitemap_entry in sitemap_urls:
                if sitemap_entry not in seen and _keyword_match(sitemap_entry):
                    queue.append(sitemap_entry)
        except Exception:
            logger.info("No se pudo usar sitemap.xml como semilla inicial.")

    while queue and len(discovered) < max_pages:
        url = canonicalize_url(queue.popleft())
        if url in seen:
            continue
        seen.add(url)
        discovered.append(url)

        try:
            response = fetch_url(url, session, delay_seconds=0)
        except Exception:
            continue

        for link in extract_internal_links(response.text, url):
            if link not in seen and (_keyword_match(link) or len(discovered) < 20):
                queue.append(link)

    filtered = [DiscoveredUrl(url=url, categoria=infer_category(url)) for url in unique_preserve_order(discovered)]
    return filtered[:max_pages]