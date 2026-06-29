from __future__ import annotations

import json
from typing import Any

from mtguard.models import (
    FusionResult,
    GateResult,
    JudgeResult,
    L1Result,
    L2Result,
    TurnTrace,
)


def l1_to_dict(r: L1Result) -> dict[str, Any]:
    return {
        "hit": r.hit,
        "rule_id": r.rule_id,
        "severity": r.severity.value if r.severity else None,
        "matched_text": r.matched_text,
    }


def l2_to_dict(r: L2Result) -> dict[str, Any]:
    return {
        "safe_score": r.safe_score,
        "proximity": r.proximity,
        "max_proximity": r.max_proximity,
        "max_region": r.max_region,
        "drift_step": r.drift_step,
        "drift_baseline": r.drift_baseline,
        "approaching_sensitive": r.approaching_sensitive,
        "trajectory_risk": r.trajectory_risk,
        "escalation_pattern": r.escalation_pattern,
        "turn_index": r.turn_index,
    }


def fusion_to_dict(r: FusionResult) -> dict[str, Any]:
    return {
        "risk_score": r.risk_score,
        "verdict": r.verdict.value,
        "factors": r.factors,
    }


def judge_to_dict(r: JudgeResult | None) -> dict[str, Any] | None:
    if r is None:
        return None
    return {
        "enabled": r.enabled,
        "invoked": r.invoked,
        "decision": r.decision,
        "reason": r.reason,
    }


def gate_to_dict(r: GateResult) -> dict[str, Any]:
    return {
        "allow_llm": r.allow_llm,
        "show_banner": r.show_banner,
        "block_reason": r.block_reason,
    }


def build_turn_trace(
    turn_index: int,
    user_message: str,
    l1: L1Result,
    l2: L2Result,
    fusion: FusionResult,
    gate: GateResult,
    judge: JudgeResult | None = None,
    latency_ms: float = 0.0,
) -> TurnTrace:
    return TurnTrace(
        turn_index=turn_index,
        user_message=user_message,
        l1=l1_to_dict(l1),
        l2=l2_to_dict(l2),
        fusion=fusion_to_dict(fusion),
        judge=judge_to_dict(judge),
        gate=gate_to_dict(gate),
        latency_ms=round(latency_ms, 2),
    )


def format_trace_panel(trace: dict[str, Any] | None) -> str:
    if not trace:
        return "*Sin turnos aún.*"
    fusion = trace.get("fusion") or {}
    l1 = trace.get("l1") or {}
    l2 = trace.get("l2") or {}
    gate = trace.get("gate") or {}
    lines = [
        f"### Turn {trace.get('turn_index', '?')}",
        f"**Verdict:** `{fusion.get('verdict', '?')}` · **Risk:** {fusion.get('risk_score', 0)}/100",
        f"**Latency:** {trace.get('latency_ms', 0)} ms",
        "",
        f"**L1** — hit={l1.get('hit')} severity={l1.get('severity')} rule={l1.get('rule_id')}",
        (
            f"**L2** — safe={l2.get('safe_score')} max_prox={l2.get('max_proximity')} "
            f"region={l2.get('max_region')} approaching={l2.get('approaching_sensitive')} "
            f"escalation={l2.get('escalation_pattern')}"
        ),
        f"**Gate** — allow_llm={gate.get('allow_llm')} banner={gate.get('show_banner')}",
    ]
    factors = fusion.get("factors") or []
    if factors:
        lines.append(f"**Factors:** {', '.join(factors)}")
    judge = trace.get("judge")
    if judge and judge.get("invoked"):
        lines.append(
            f"**Judge** — {judge.get('decision')} · {judge.get('reason', '')}"
        )
    return "\n".join(lines)


def format_layers_modal(trace: dict[str, Any] | None) -> str:
    if not trace:
        return "No hay datos de capas para este turno."
    sections = []
    for layer in ("l1", "l2", "fusion", "judge", "gate"):
        data = trace.get(layer)
        if data is not None:
            sections.append(f"#### {layer.upper()}\n```json\n{json.dumps(data, indent=2)}\n```")
    return "\n\n".join(sections)
