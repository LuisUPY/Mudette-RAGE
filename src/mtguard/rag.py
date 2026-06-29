from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import faiss

from mtguard.embedder import Embedder


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class KnowledgeBase:
    """FAISS-backed RAG over demo pack kb/."""

    def __init__(self, kb_dir: Path, embedder: Embedder | None = None) -> None:
        self.kb_dir = kb_dir
        self.embedder = embedder or Embedder()
        self._chunks: list[dict] = json.loads((kb_dir / "chunks.json").read_text(encoding="utf-8"))
        self._index = faiss.read_index(str(kb_dir / "index.faiss"))

    @classmethod
    def from_pack_dir(cls, pack_dir: Path, embedder: Embedder | None = None) -> KnowledgeBase:
        return cls(pack_dir / "kb", embedder=embedder)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        if not self._chunks or self._index.ntotal == 0:
            return []

        k = min(top_k, len(self._chunks))
        vec = self.embedder.embed(query).reshape(1, -1)
        scores, indices = self._index.search(vec, k)

        results: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self._chunks[idx]
            results.append(
                RetrievedChunk(
                    text=chunk["text"],
                    source=chunk["source"],
                    score=float(score),
                )
            )
        return results
