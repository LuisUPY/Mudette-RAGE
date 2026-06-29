from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(str, Enum):
    CLEAR = "CLEAR"
    WATCH = "WATCH"
    ALERT = "ALERT"
    CONTAIN = "CONTAIN"


@dataclass
class L1Result:
    hit: bool
    rule_id: str | None = None
    severity: Severity | None = None
    matched_text: str | None = None


@dataclass
class L2Result:
    safe_score: float = 0.0
    proximity: dict[str, float] = field(default_factory=dict)
    max_proximity: float = 0.0
    max_region: str | None = None
    drift_step: float = 0.0
    drift_baseline: float = 0.0
    approaching_sensitive: bool = False
    trajectory_risk: float = 0.0
    escalation_pattern: bool = False
    turn_index: int = 0


@dataclass
class FusionResult:
    risk_score: int = 0
    verdict: Verdict = Verdict.CLEAR
    factors: list[str] = field(default_factory=list)


@dataclass
class JudgeResult:
    enabled: bool = False
    invoked: bool = False
    decision: str | None = None  # ALLOW | DENY
    reason: str | None = None


@dataclass
class GateResult:
    allow_llm: bool = True
    show_banner: bool = False
    block_reason: str | None = None


@dataclass
class TurnTrace:
    turn_index: int
    user_message: str
    l1: dict[str, Any]
    l2: dict[str, Any] | None = None
    fusion: dict[str, Any] | None = None
    judge: dict[str, Any] | None = None
    gate: dict[str, Any] | None = None
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "user_message": self.user_message,
            "l1": self.l1,
            "l2": self.l2,
            "fusion": self.fusion,
            "judge": self.judge,
            "gate": self.gate,
            "latency_ms": self.latency_ms,
        }
