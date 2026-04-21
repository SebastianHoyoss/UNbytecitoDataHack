from __future__ import annotations

import logging
import time
from functools import lru_cache
from html import unescape
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def build_session(user_agent: str, retries: int = 3, backoff_factor: float = 0.75) -> Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent, "Accept-Language": "es-CO,es;q=0.9"})
    return session


@lru_cache(maxsize=64)
def _robots_parser(robots_url: str) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        logger.warning("No fue posible leer robots.txt: %s", robots_url)
    return parser


def robots_allowed(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = _robots_parser(robots_url)
    try:
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True


def fetch_url(
    url: str,
    session: Session,
    delay_seconds: float = 0.0,
    timeout: int = 30,
) -> Response:
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def canonicalize_url(url: str) -> str:
    clean_url, _ = urldefrag(url)
    return clean_url.rstrip("/") if clean_url.endswith("/") else clean_url


def is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def extract_internal_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute_url = canonicalize_url(urljoin(base_url, href))
        if is_same_domain(absolute_url, base_url):
            links.append(absolute_url)
    return links


def parse_html_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string
    if not title:
        meta_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content"):
            title = meta_title["content"]
    return unescape(title).strip()


def detect_language(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    html_tag = soup.find("html")
    language = html_tag.get("lang") if html_tag else None
    return (language or "es").split("-")[0].lower()