from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from mtguard.embedder import Embedder
from mtguard.gates.user_gate import UserGate
from mtguard.judge import EscalationJudge
from mtguard.layers.fusion import RiskFusion
from mtguard.layers.l1_regex import RegexGuard
from mtguard.layers.l2_trajectory import TrajectoryGuard
from mtguard.models import FusionResult, GateResult, JudgeResult, TurnTrace
from mtguard.nim import DEFAULT_JUDGE_MODEL, DEFAULT_MAIN_MODEL, NIM_BASE_URL
from mtguard.pack_loader import DemoPack
from mtguard.pipeline import MTGuardPipeline
from mtguard.rag import KnowledgeBase

_MAIN_API_KEY_ERROR = (
    "Error Crítico: No se detectó la NVIDIA API Key principal para Nexa Copilot."
)
_JUDGE_API_KEY_ERROR = (
    "Error Crítico: El Juez de Escalación está activo pero requiere una NVIDIA API Key "
    "válida para el modelo mini juez."
)

_ALERT_BANNER = "[Security Notice] This conversation turn was flagged for elevated risk.\n\n"


@dataclass
class AgentTurn:
    trace: TurnTrace
    response: str
    fusion: FusionResult
    gate: GateResult


def _require_main_api_key(api_key: str | None) -> str:
    key = (api_key or "").strip()
    if not key:
        raise ValueError(_MAIN_API_KEY_ERROR)
    return key


@dataclass
class NexaAgent:
    """Pack-driven agent — responses via NVIDIA NIM API only (RAG context + LLM)."""

    pack: DemoPack
    kb: KnowledgeBase
    main_api_key: str
    main_model: str = DEFAULT_MAIN_MODEL
    system_prompt: str = field(init=False)
    secret_patterns: list[re.Pattern[str]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.main_api_key = _require_main_api_key(self.main_api_key)
        self.system_prompt = self.pack.system_prompt
        vault_path = self.pack.pack_dir / "secrets_vault.json"
        vault = json.loads(vault_path.read_text(encoding="utf-8"))
        secrets = vault.get("secrets", {})
        self.secret_patterns = [
            re.compile(re.escape(str(v)), re.IGNORECASE) for v in secrets.values() if v
        ]

    @classmethod
    def from_pack(
        cls,
        pack: DemoPack,
        embedder: Embedder | None = None,
        main_api_key: str | None = None,
        main_model: str = DEFAULT_MAIN_MODEL,
    ) -> NexaAgent:
        embedder = embedder or Embedder()
        return cls(
            pack=pack,
            kb=KnowledgeBase.from_pack_dir(pack.pack_dir, embedder=embedder),
            main_api_key=_require_main_api_key(main_api_key),
            main_model=main_model,
        )

    def respond(
        self,
        message: str,
        gate: GateResult,
        fusion: FusionResult | None = None,
    ) -> str:
        if not gate.allow_llm:
            return self._scrub_secrets(self._block_message())

        body = self._compose_online(message)
        if gate.show_banner:
            body = _ALERT_BANNER + body
        return self._scrub_secrets(body)

    def _block_message(self) -> str:
        org = self.pack.agent_profile.get("organization", self.pack.display_name)
        return (
            f"I cannot assist with that request. It has been blocked by {org} security policy. "
            "If you believe this is an error, please contact your IT support team."
        )

    def _compose_online(self, message: str) -> str:
        _require_main_api_key(self.main_api_key)

        chunks = self.kb.search(message, top_k=3)
        context = "\n\n---\n\n".join(c.text for c in chunks) if chunks else ""
        rag_block = f"Knowledge base excerpts:\n{context}\n\n" if context else ""
        user_content = f"{rag_block}Employee question:\n{message}"
        return self._call_main_llm(user_content)

    def _call_main_llm(self, user_content: str) -> str:
        from openai import OpenAI

        client = OpenAI(
            base_url=NIM_BASE_URL,
            api_key=self.main_api_key,
        )
        response = client.chat.completions.create(
            model=self.main_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("NVIDIA NIM devolvió una respuesta vacía.")
        return content

    def _scrub_secrets(self, text: str) -> str:
        for pattern in self.secret_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text


class MTGuardSession:
    """Full stack: defense pipeline + Nexa agent + optional EscalationJudge."""

    def __init__(
        self,
        pack: DemoPack,
        embedder: Embedder | None = None,
        pipeline: MTGuardPipeline | None = None,
        agent: NexaAgent | None = None,
        judge: EscalationJudge | None = None,
        main_api_key: str | None = None,
        judge_api_key: str | None = None,
        judge_enabled: bool = False,
        main_model: str = DEFAULT_MAIN_MODEL,
        judge_model: str = DEFAULT_JUDGE_MODEL,
    ) -> None:
        self.pack = pack
        self.embedder = embedder or Embedder()
        self.pipeline = pipeline or self._build_pipeline()

        resolved_main = _require_main_api_key(main_api_key)
        self.agent = agent or NexaAgent.from_pack(
            pack,
            self.embedder,
            main_api_key=resolved_main,
            main_model=main_model,
        )

        if judge is not None:
            self.judge = judge
        elif judge_enabled:
            judge_key = (judge_api_key or "").strip()
            if not judge_key:
                raise ValueError(_JUDGE_API_KEY_ERROR)
            self.judge = EscalationJudge(
                pack=pack,
                api_key=judge_key,
                model=judge_model,
                enabled=True,
            )
        else:
            self.judge = None
        self.state = self.pipeline.reset()

    @classmethod
    def from_pack_dir(
        cls,
        pack_dir: Path | str,
        main_api_key: str | None = None,
        judge_api_key: str | None = None,
        judge_enabled: bool = False,
        main_model: str = DEFAULT_MAIN_MODEL,
        judge_model: str = DEFAULT_JUDGE_MODEL,
    ) -> MTGuardSession:
        pack = DemoPack.load(Path(pack_dir))
        return cls(
            pack,
            main_api_key=main_api_key,
            judge_api_key=judge_api_key,
            judge_enabled=judge_enabled,
            main_model=main_model,
            judge_model=judge_model,
        )

    def _build_pipeline(self) -> MTGuardPipeline:
        return MTGuardPipeline(
            l1=RegexGuard(),
            l2=TrajectoryGuard(self.pack.agent_profile, embedder=self.embedder),
            fusion=RiskFusion(),
            gate=UserGate(),
        )

    def reset(self) -> None:
        self.state = self.pipeline.reset()

    def turn(self, message: str, judge_override: JudgeResult | None = None) -> AgentTurn:
        trace, self.state, fusion = self.pipeline.process_turn(
            message,
            self.state,
            judge=judge_override,
            auto_judge=self.judge,
        )
        gate = GateResult(
            allow_llm=trace.gate["allow_llm"],  # type: ignore[index]
            show_banner=trace.gate["show_banner"],  # type: ignore[index]
            block_reason=trace.gate.get("block_reason"),  # type: ignore[union-attr]
        )
        response = self.agent.respond(message, gate, fusion)
        return AgentTurn(trace=trace, response=response, fusion=fusion, gate=gate)
