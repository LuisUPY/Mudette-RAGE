from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

EMBED_DIM = 2048


class Embedder:
    """Shared 2048-d HashingVectorizer embedder for L2 defense and RAG."""

    def __init__(self, n_features: int = EMBED_DIM) -> None:
        self.n_features = n_features
        self._vectorizer = HashingVectorizer(
            n_features=n_features, alternate_sign=False, norm="l2"
        )

    def embed(self, text: str) -> np.ndarray:
        return self._vectorizer.transform([text]).toarray()[0].astype(np.float32)

    def embed_many(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.n_features), dtype=np.float32)
        return self._vectorizer.transform(texts).toarray().astype(np.float32)

    @staticmethod
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))

    def centroid(self, texts: list[str]) -> np.ndarray:
        vecs = self.embed_many(texts)
        center = vecs.mean(axis=0)
        norm = np.linalg.norm(center)
        if norm > 0:
            center = center / norm
        return center.astype(np.float32)

    @property
    def vectorizer(self) -> HashingVectorizer:
        return self._vectorizer
