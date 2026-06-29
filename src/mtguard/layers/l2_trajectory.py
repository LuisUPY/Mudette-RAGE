from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from mtguard.embedder import Embedder
from mtguard.models import L2Result

APPROACH_THRESHOLD = 0.62
EWMA_ALPHA = 0.25


@dataclass
class ConversationState:
    turn_index: int = -1
    turn_embeddings: list[np.ndarray] = field(default_factory=list)
    proximity_history: list[dict[str, float]] = field(default_factory=list)
    drift_history: list[float] = field(default_factory=list)
    trajectory_ewma: float = 0.0


class TrajectoryGuard:
    """L2 vector proximity and multi-turn trajectory analysis."""

    def __init__(
        self,
        agent_profile: dict,
        embedder: Embedder | None = None,
    ) -> None:
        self._embedder = embedder or Embedder()
        self._safe_centroid = self._embedder.centroid(agent_profile["allowed_intent_examples"])
        self._region_centroids: dict[str, np.ndarray] = {}
        for name, region in agent_profile["sensitive_regions"].items():
            self._region_centroids[name] = self._embedder.centroid(region["seed_phrases"])
        self._drift_baseline = self._compute_drift_baseline(
            agent_profile["allowed_intent_examples"]
        )

    @classmethod
    def from_profile_path(cls, path: Path, embedder: Embedder | None = None) -> TrajectoryGuard:
        profile = json.loads(path.read_text(encoding="utf-8"))
        return cls(profile, embedder=embedder)

    def _compute_drift_baseline(self, safe_texts: list[str]) -> float:
        if len(safe_texts) < 2:
            return 0.0
        vecs = self._embedder.embed_many(safe_texts)
        drifts = [
            1.0 - self._embedder.cosine(vecs[i], vecs[i + 1])
            for i in range(len(vecs) - 1)
        ]
        return float(np.mean(drifts)) if drifts else 0.0

    def reset(self) -> ConversationState:
        return ConversationState()

    def evaluate(self, message: str, state: ConversationState | None = None) -> tuple[L2Result, ConversationState]:
        state = state or ConversationState()
        e_t = self._embedder.embed(message)

        safe_score = self._embedder.cosine(e_t, self._safe_centroid)
        proximity: dict[str, float] = {
            name: self._embedder.cosine(e_t, centroid)
            for name, centroid in self._region_centroids.items()
        }
        max_region = max(proximity, key=proximity.get) if proximity else None
        max_proximity = proximity[max_region] if max_region else 0.0

        if state.turn_embeddings:
            drift_step = 1.0 - self._embedder.cosine(e_t, state.turn_embeddings[-1])
        else:
            drift_step = 0.0

        approaching_sensitive = max_proximity >= APPROACH_THRESHOLD and max_proximity > safe_score
        trajectory_risk = self._update_ewma(state, max_proximity)
        escalation_pattern = self._detect_escalation(state, proximity)

        state.turn_index += 1
        state.turn_embeddings.append(e_t)
        state.proximity_history.append(dict(proximity))
        state.drift_history.append(drift_step)

        result = L2Result(
            safe_score=round(safe_score, 4),
            proximity={k: round(v, 4) for k, v in proximity.items()},
            max_proximity=round(max_proximity, 4),
            max_region=max_region,
            drift_step=round(drift_step, 4),
            drift_baseline=round(self._drift_baseline, 4),
            approaching_sensitive=approaching_sensitive,
            trajectory_risk=round(trajectory_risk, 4),
            escalation_pattern=escalation_pattern,
            turn_index=state.turn_index,
        )
        return result, state

    @staticmethod
    def _update_ewma(state: ConversationState, max_proximity: float) -> float:
        if state.turn_index < 0:
            state.trajectory_ewma = max_proximity
        else:
            state.trajectory_ewma = (
                EWMA_ALPHA * max_proximity + (1 - EWMA_ALPHA) * state.trajectory_ewma
            )
        return state.trajectory_ewma

    @staticmethod
    def _detect_escalation(state: ConversationState, current: dict[str, float]) -> bool:
        if state.turn_index < 2:
            return False
        prev1 = state.proximity_history[-1]
        prev2 = state.proximity_history[-2]
        for region, score in current.items():
            if prev2.get(region, 0.0) < prev1.get(region, 0.0) < score:
                return True
        return False
