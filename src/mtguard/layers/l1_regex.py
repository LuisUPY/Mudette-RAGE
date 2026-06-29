from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path

from mtguard.models import L1Result, Severity


class RegexGuard:
    """L1 rule-based guard. High precision over recall."""

    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(rules_path: Path | None) -> list[dict]:
        if rules_path is not None:
            raw = rules_path.read_text(encoding="utf-8")
        else:
            raw = resources.files("mtguard").joinpath("rules.json").read_text(encoding="utf-8")
        rules = json.loads(raw)
        if len(rules) > 40:
            raise ValueError(f"L1 rules exceed limit: {len(rules)} > 40")
        return rules

    def scan(self, message: str) -> L1Result:
        if not message or not message.strip():
            return L1Result(hit=False)

        best: L1Result | None = None
        severity_rank = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}

        for rule in self._rules:
            pattern = re.compile(rule["pattern"])
            match = pattern.search(message)
            if not match:
                continue
            severity = Severity(rule["severity"])
            candidate = L1Result(
                hit=True,
                rule_id=rule["id"],
                severity=severity,
                matched_text=match.group(0),
            )
            if best is None or severity_rank[severity] > severity_rank[best.severity]:  # type: ignore[index]
                best = candidate

        return best if best is not None else L1Result(hit=False)

    @property
    def rule_count(self) -> int:
        return len(self._rules)
