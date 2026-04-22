from __future__ import annotations

from functools import lru_cache
from typing import Protocol

import numpy as np


class EmbeddingProvider(Protocol):
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = self._load_model(model_name)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_model(model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Falta instalar sentence-transformers. Revisa requirements.txt."
            ) from exc

        return SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=float).tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vector, dtype=float).tolist()


def build_embedding_provider(model_name: str) -> SentenceTransformerEmbeddingProvider:
    return SentenceTransformerEmbeddingProvider(model_name=model_name)