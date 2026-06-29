from __future__ import annotations

import json
from dataclasses import dataclass

from mtguard.models import FusionResult, JudgeResult, L1Result, L2Result, Verdict
from mtguard.pack_loader import DemoPack
from mtguard.trace import fusion_to_dict, l1_to_dict, l2_to_dict

DEFAULT_JUDGE_THRESHOLD = 55
DEFAULT_JUDGE_MODEL = "gpt-4o-mini"


@dataclass
class EscalationJudge:
    """LLM judge — lightweight model, separate API key from main agent."""

    pack: DemoPack
    api_key: str
    model: str = DEFAULT_JUDGE_MODEL
    threshold: int = DEFAULT_JUDGE_THRESHOLD
    enabled: bool = True

    def should_invoke(self, fusion: FusionResult) -> bool:
        if not self.enabled or not self.api_key:
            return False
        if fusion.verdict == Verdict.CONTAIN:
            return False
        if fusion.verdict not in (Verdict.WATCH, Verdict.ALERT):
            return False
        return fusion.risk_score >= self.threshold

    def evaluate(
        self,
        message: str,
        l1: L1Result,
        l2: L2Result,
        fusion: FusionResult,
    ) -> JudgeResult:
        if not self.should_invoke(fusion):
            return JudgeResult(enabled=self.enabled, invoked=False)

        prompt = self._build_prompt(message, l1, l2, fusion)
        try:
            raw = self._call_llm(prompt)
            decision, reason = parse_judge_response(raw)
            return JudgeResult(
                enabled=True,
                invoked=True,
                decision=decision,
                reason=reason,
            )
        except Exception as exc:  # noqa: BLE001 — demo fallback to ALLOW bias
            return JudgeResult(
                enabled=True,
                invoked=False,
                decision=None,
                reason=f"judge_error: {exc}",
            )

    def _build_prompt(
        self,
        message: str,
        l1: L1Result,
        l2: L2Result,
        fusion: FusionResult,
    ) -> str:
        context = {
            "user_message": message,
            "l1": l1_to_dict(l1),
            "l2": l2_to_dict(l2),
            "fusion": fusion_to_dict(fusion),
        }
        return (
            f"{self.pack.judge_prompt}\n\n"
            f"CONTEXT (JSON):\n{json.dumps(context, indent=2)}\n\n"
            "Decision:"
        )

    def _call_llm(self, user_prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are the Escalation Judge. One line only."},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=120,
            temperature=0,
        )
        return (response.choices[0].message.content or "").strip()


def parse_judge_response(text: str) -> tuple[str, str]:
    """Parse ALLOW/DENY with bias toward ALLOW on ambiguity."""
    line = text.strip().split("\n")[0].strip()
    upper = line.upper()
    if upper.startswith("DENY"):
        reason = _split_reason(line)
        return "DENY", reason
    if upper.startswith("ALLOW"):
        return "ALLOW", _split_reason(line)
    if "DENY" in upper and "ALLOW" not in upper:
        return "DENY", line
    return "ALLOW", line or "default_allow"


def _split_reason(line: str) -> str:
    for sep in ("—", "-", ":"):
        if sep in line:
            parts = line.split(sep, 1)
            if len(parts) == 2:
                return parts[1].strip()
    return line
