from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\t\f\v]+", " ", normalized)
    normalized = re.sub(r"[ ]{2,}", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def clean_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(\w)", r"\1 \2", text)
    return text.strip()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def infer_category(url: str, title: str = "") -> str:
    haystack = f"{url} {title}".lower()
    mapping = {
        "admis": "admisiones",
        "inscrip": "inscripciones",
        "costo": "costos",
        "matric": "costos",
        "pregrado": "oferta_academica",
        "posgrado": "oferta_academica",
        "especializ": "oferta_academica",
        "tecnolog": "oferta_academica",
        "programa": "oferta_academica",
        "requisit": "requisitos_admision",
    }
    for keyword, category in mapping.items():
        if keyword in haystack:
            return category
    return "general"


def _word_chunks(words: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    overlap = max(0, min(chunk_overlap, chunk_size - 1))
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 180) -> list[str]:
    text = clean_text(text)
    if not text:
        return []

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", normalize_text(text)) if paragraph.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= chunk_size:
            current = paragraph
            continue

        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", paragraph) if sentence.strip()]
        if not sentences:
            sentences = [paragraph]
        for sentence in sentences:
            if len(sentence) <= chunk_size:
                if not current:
                    current = sentence
                elif len(f"{current} {sentence}") <= chunk_size:
                    current = f"{current} {sentence}"
                else:
                    chunks.append(current)
                    current = sentence
            else:
                if current:
                    chunks.append(current)
                    current = ""
                sentence_words = sentence.split()
                chunks.extend(_word_chunks(sentence_words, chunk_size, chunk_overlap))

    if current:
        chunks.append(current)

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered