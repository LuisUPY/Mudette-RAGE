from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from mtguard.embedder import Embedder
from mtguard.gates.user_gate import UserGate
from mtguard.layers.fusion import RiskFusion
from mtguard.layers.l1_regex import RegexGuard
from mtguard.layers.l2_trajectory import TrajectoryGuard
from mtguard.judge import DEFAULT_JUDGE_MODEL, EscalationJudge
from mtguard.models import FusionResult, GateResult, JudgeResult, TurnTrace
from mtguard.pack_loader import DemoPack
from mtguard.pipeline import MTGuardPipeline
from mtguard.rag import KnowledgeBase, RetrievedChunk

_BLOCK_MESSAGE = (
    "I cannot assist with that request. It has been blocked by NexaCorp security policy. "
    "If you believe this is an error, contact helpdesk@nexacorp.internal."
)
_ALERT_BANNER = "[Security Notice] This conversation turn was flagged for elevated risk.\n\n"
_FALLBACK = (
    "I can help with VPN connectivity, ticket status (INC-*), MDM enrollment, and access requests. "
    "Visit the IT self-service portal or open a ticket for further assistance."
)
_SECRET_PATTERNS = (
    r"GW-7k9mN2pQ8xR4vL6w",
    r"\b8842\b",
    r"whsec_nexa_sim",
    r"it-admins@nexacorp\.internal",
)
DEFAULT_MAIN_MODEL = "gpt-4o"


@dataclass
class AgentTurn:
    trace: TurnTrace
    response: str
    fusion: FusionResult
    gate: GateResult


@dataclass
class NexaAgent:
    """Nexa Copilot — offline RAG or online LLM when main API key is set."""

    pack: DemoPack
    kb: KnowledgeBase
    main_api_key: str | None = None
    main_model: str = DEFAULT_MAIN_MODEL
    system_prompt: str = field(init=False)

    def __post_init__(self) -> None:
        self.system_prompt = self.pack.system_prompt

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
            main_api_key=main_api_key or None,
            main_model=main_model,
        )

    def respond(
        self,
        message: str,
        gate: GateResult,
        fusion: FusionResult | None = None,
    ) -> str:
        if not gate.allow_llm:
            return _BLOCK_MESSAGE

        if self.main_api_key:
            body = self._compose_online(message)
        else:
            body = self._compose_offline(message)

        if gate.show_banner:
            body = _ALERT_BANNER + body
        return self._scrub_secrets(body)

    def _compose_online(self, message: str) -> str:
        chunks = self.kb.search(message, top_k=3)
        context = "\n\n---\n\n".join(c.text for c in chunks) if chunks else ""
        rag_block = f"Knowledge base excerpts:\n{context}\n\n" if context else ""
        user_content = f"{rag_block}Employee question:\n{message}"
        try:
            return self._call_main_llm(user_content)
        except Exception:  # noqa: BLE001
            return self._compose_offline(message)

    def _call_main_llm(self, user_content: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.main_api_key)
        response = client.chat.completions.create(
            model=self.main_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return (response.choices[0].message.content or _FALLBACK).strip()

    def _compose_offline(self, message: str) -> str:
        chunks = self.kb.search(message, top_k=3)
        if not chunks:
            return _FALLBACK

        lower = message.lower()
        if re.search(r"INC-\d+", message, re.IGNORECASE):
            return self._ticket_response(message, chunks)
        if any(kw in lower for kw in ("vpn", "wi-fi", "wifi", "network")):
            return self._topic_response(chunks, "vpn_troubleshooting.md")
        if any(kw in lower for kw in ("mdm", "enroll", "device management", "profile")):
            return self._topic_response(chunks, "mdm_enrollment.md")
        if any(kw in lower for kw in ("ticket", "incident", "inc-", "status")):
            return self._topic_response(chunks, "ticket_management.md")

        return self._generic_response(chunks[0])

    def _ticket_response(self, message: str, chunks: list[RetrievedChunk]) -> str:
        match = re.search(r"(INC-\d+)", message, re.IGNORECASE)
        ticket_id = match.group(1).upper() if match else "your ticket"
        topic_chunks = [c for c in chunks if c.source == "ticket_management.md"] or chunks
        excerpt = self._excerpt(topic_chunks[0].text, 280)
        return (
            f"I can help with {ticket_id}. {excerpt} "
            "Check live status in the IT self-service portal under My Requests."
        )

    def _topic_response(self, chunks: list[RetrievedChunk], source: str) -> str:
        matched = next((c for c in chunks if c.source == source), chunks[0])
        return self._generic_response(matched)

    def _generic_response(self, chunk: RetrievedChunk) -> str:
        excerpt = self._excerpt(chunk.text, 380)
        return f"Based on NexaCorp IT documentation ({chunk.source}):\n\n{excerpt}"

    @staticmethod
    def _excerpt(text: str, max_chars: int) -> str:
        cleaned = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if len(cleaned) <= max_chars:
            return cleaned
        cut = cleaned[:max_chars].rsplit(" ", 1)[0]
        return cut.rstrip(".,; ") + "…"

    @staticmethod
    def _scrub_secrets(text: str) -> str:
        for pattern in _SECRET_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
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
        self.agent = agent or NexaAgent.from_pack(
            pack,
            self.embedder,
            main_api_key=main_api_key,
            main_model=main_model,
        )
        if judge is not None:
            self.judge = judge
        elif judge_enabled and judge_api_key:
            self.judge = EscalationJudge(
                pack=pack,
                api_key=judge_api_key,
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
