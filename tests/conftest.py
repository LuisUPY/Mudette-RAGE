"""Shared pytest fixtures — mock NVIDIA NIM for CI without real API keys."""

from __future__ import annotations

import pytest

from mtguard.agent import NexaAgent
from mtguard.judge import EscalationJudge

TEST_MAIN_API_KEY = "nvapi-test-main-mock"
TEST_JUDGE_API_KEY = "nvapi-test-judge-mock"


@pytest.fixture
def main_api_key() -> str:
    return TEST_MAIN_API_KEY


@pytest.fixture
def judge_api_key() -> str:
    return TEST_JUDGE_API_KEY


@pytest.fixture(autouse=True)
def mock_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_main_llm(self: NexaAgent, user_content: str) -> str:
        if "INC-48291" in user_content:
            return "Ticket INC-48291 is In Progress. Check the self-service portal."
        if "vpn" in user_content.lower():
            return "Try restarting the NexaVPN client from the menu bar."
        return "Mocked Nexa Copilot response powered by API."

    def fake_judge_llm(self: EscalationJudge, user_prompt: str) -> str:
        return "ALLOW — mocked judge evaluation"

    monkeypatch.setattr(NexaAgent, "_call_main_llm", fake_main_llm)
    monkeypatch.setattr(EscalationJudge, "_call_llm", fake_judge_llm)
