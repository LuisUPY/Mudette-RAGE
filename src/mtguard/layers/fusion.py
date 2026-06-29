from __future__ import annotations

from mtguard.models import (
    FusionResult,
    GateResult,
    JudgeResult,
    L1Result,
    L2Result,
    Severity,
    Verdict,
)

SAFE_SCORE_VETO = 0.55
TRAJECTORY_HIGH = 0.10
PROXIMITY_HIGH = 0.18

_WEIGHTS = {
    "l1_high": 45,
    "l1_medium": 25,
    "approaching_sensitive": 20,
    "escalation": 15,
    "trajectory_high": 10,
    "proximity_high": 10,
}
_L1_HIGH_FLOOR = 75


class RiskFusion:
    """Combine L1 + L2 signals into risk_score (0–100) and verdict."""

    def fuse(self, l1: L1Result, l2: L2Result) -> FusionResult:
        score = 0
        factors: list[str] = []
        l1_high = l1.hit and l1.severity == Severity.HIGH

        if l1_high:
            score += _WEIGHTS["l1_high"]
            factors.append("l1_high")
        elif l1.hit and l1.severity == Severity.MEDIUM:
            score += _WEIGHTS["l1_medium"]
            factors.append("l1_medium")

        if l2.approaching_sensitive:
            score += _WEIGHTS["approaching_sensitive"]
            factors.append("approaching_sensitive")

        if l2.escalation_pattern:
            score += _WEIGHTS["escalation"]
            factors.append("escalation")

        if l2.trajectory_risk >= TRAJECTORY_HIGH:
            score += _WEIGHTS["trajectory_high"]
            factors.append("trajectory_high")

        if l2.max_proximity >= PROXIMITY_HIGH:
            score += _WEIGHTS["proximity_high"]
            factors.append("proximity_high")

        if l1_high:
            score = max(score, _L1_HIGH_FLOOR)

        score = min(score, 100)
        verdict = self._verdict_from_score(score)

        if l1_high:
            verdict = Verdict.CONTAIN
        elif l2.safe_score >= SAFE_SCORE_VETO and verdict == Verdict.CONTAIN:
            verdict = Verdict.ALERT
            factors.append("safe_score_veto")

        return FusionResult(risk_score=score, verdict=verdict, factors=factors)

    @staticmethod
    def _verdict_from_score(score: int) -> Verdict:
        if score >= 75:
            return Verdict.CONTAIN
        if score >= 45:
            return Verdict.ALERT
        if score >= 25:
            return Verdict.WATCH
        return Verdict.CLEAR

    def apply_judge_deny(self, fusion: FusionResult) -> FusionResult:
        """Upgrade verdict to CONTAIN when judge denies (Phase 6 hook)."""
        if fusion.verdict != Verdict.CONTAIN:
            return FusionResult(
                risk_score=max(fusion.risk_score, _L1_HIGH_FLOOR),
                verdict=Verdict.CONTAIN,
                factors=[*fusion.factors, "judge_deny"],
            )
        return fusion
