from __future__ import annotations

from mtguard.models import FusionResult, GateResult, JudgeResult, Verdict


class UserGate:
    """Gate LLM access based on fusion verdict and optional judge decision."""

    def evaluate(
        self,
        fusion: FusionResult,
        judge: JudgeResult | None = None,
    ) -> GateResult:
        if judge and judge.invoked and judge.decision == "DENY":
            return GateResult(
                allow_llm=False,
                show_banner=False,
                block_reason="judge_deny",
            )

        if fusion.verdict == Verdict.CONTAIN:
            return GateResult(
                allow_llm=False,
                show_banner=False,
                block_reason="contain",
            )

        if fusion.verdict == Verdict.ALERT:
            return GateResult(
                allow_llm=True,
                show_banner=True,
                block_reason=None,
            )

        return GateResult(allow_llm=True, show_banner=False, block_reason=None)
