import re
import io
import requests
from pypdf import PdfReader


def get_arxiv_id(url: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5})", url)
    if match:
        return match.group(1)
    return url.rstrip("/").split("/")[-1]


def download_and_extract(url: str) -> str:
    arxiv_id = get_arxiv_id(url)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    response = requests.get(pdf_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    reader = PdfReader(io.BytesIO(response.content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return text.strip()
