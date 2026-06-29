"""Tests for FAISS RAG knowledge base."""

from __future__ import annotations

from pathlib import Path

import pytest

from mtguard.embedder import Embedder
from mtguard.rag import KnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "demo_pack" / "nexa_copilot"


@pytest.fixture
def kb() -> KnowledgeBase:
    return KnowledgeBase.from_pack_dir(PACK_DIR)


class TestKnowledgeBase:
    def test_chunk_count(self, kb: KnowledgeBase) -> None:
        assert kb.chunk_count == 10

    def test_search_vpn(self, kb: KnowledgeBase) -> None:
        results = kb.search("VPN disconnecting after macOS update")
        assert len(results) >= 1
        sources = {r.source for r in results}
        assert "vpn_troubleshooting.md" in sources

    def test_search_ticket(self, kb: KnowledgeBase) -> None:
        results = kb.search("ticket INC-48291 status lookup")
        assert len(results) >= 1
        assert any(r.source == "ticket_management.md" for r in results)

    def test_search_mdm(self, kb: KnowledgeBase) -> None:
        results = kb.search("MDM enrollment macOS profile")
        assert len(results) >= 1
        assert any(r.source == "mdm_enrollment.md" for r in results)

    def test_scores_descending(self, kb: KnowledgeBase) -> None:
        results = kb.search("VPN password reset", top_k=3)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_shared_embedder(self) -> None:
        embedder = Embedder()
        kb = KnowledgeBase.from_pack_dir(PACK_DIR, embedder=embedder)
        vec = embedder.embed("test")
        assert vec.shape[0] == embedder.n_features
        assert kb.search("VPN")[0].score > 0
