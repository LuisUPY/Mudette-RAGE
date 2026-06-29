"""Tests for UserGate."""

from __future__ import annotations

import pytest

from mtguard.gates.user_gate import UserGate
from mtguard.models import FusionResult, JudgeResult, Verdict


@pytest.fixture
def gate() -> UserGate:
    return UserGate()


class TestUserGate:
    def test_clear_allows_llm(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=10, verdict=Verdict.CLEAR)
        result = gate.evaluate(fusion)
        assert result.allow_llm is True
        assert result.show_banner is False

    def test_watch_allows_no_banner(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=30, verdict=Verdict.WATCH)
        result = gate.evaluate(fusion)
        assert result.allow_llm is True
        assert result.show_banner is False

    def test_alert_allows_with_banner(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=50, verdict=Verdict.ALERT)
        result = gate.evaluate(fusion)
        assert result.allow_llm is True
        assert result.show_banner is True

    def test_contain_blocks_llm(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=80, verdict=Verdict.CONTAIN)
        result = gate.evaluate(fusion)
        assert result.allow_llm is False
        assert result.block_reason == "contain"

    def test_judge_deny_blocks_llm(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=30, verdict=Verdict.WATCH)
        judge = JudgeResult(enabled=True, invoked=True, decision="DENY", reason="malicious")
        result = gate.evaluate(fusion, judge)
        assert result.allow_llm is False
        assert result.block_reason == "judge_deny"

    def test_judge_allow_on_alert(self, gate: UserGate) -> None:
        fusion = FusionResult(risk_score=50, verdict=Verdict.ALERT)
        judge = JudgeResult(enabled=True, invoked=True, decision="ALLOW", reason="ok")
        result = gate.evaluate(fusion, judge)
        assert result.allow_llm is True
        assert result.show_banner is True
