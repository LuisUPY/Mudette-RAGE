from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FILES = (
    "agent_profile.json",
    "system_prompt.txt",
    "secrets_vault.json",
    "judge_prompt.txt",
    "attack_playbook.json",
    "benign_playbook.json",
)

REQUIRED_KB_FILES = ("index.faiss", "chunks.json", "manifest.json")


@dataclass(frozen=True)
class DemoPack:
    pack_id: str
    pack_dir: Path
    agent_profile: dict
    system_prompt: str
    secrets_vault: dict
    judge_prompt: str
    attack_playbook: dict
    benign_playbook: dict
    kb_dir: Path

    @classmethod
    def load(cls, pack_dir: Path) -> DemoPack:
        pack_dir = pack_dir.resolve()
        if not pack_dir.is_dir():
            raise FileNotFoundError(f"Pack directory not found: {pack_dir}")

        missing = [name for name in REQUIRED_FILES if not (pack_dir / name).exists()]
        if missing:
            raise FileNotFoundError(f"Pack missing files: {', '.join(missing)}")

        kb_dir = pack_dir / "kb"
        kb_missing = [name for name in REQUIRED_KB_FILES if not (kb_dir / name).exists()]
        if kb_missing:
            raise FileNotFoundError(f"KB missing files: {', '.join(kb_missing)}")

        profile = json.loads((pack_dir / "agent_profile.json").read_text(encoding="utf-8"))
        pack_id = profile.get("agent_id", pack_dir.name)

        return cls(
            pack_id=pack_id,
            pack_dir=pack_dir,
            agent_profile=profile,
            system_prompt=(pack_dir / "system_prompt.txt").read_text(encoding="utf-8").strip(),
            secrets_vault=json.loads((pack_dir / "secrets_vault.json").read_text(encoding="utf-8")),
            judge_prompt=(pack_dir / "judge_prompt.txt").read_text(encoding="utf-8").strip(),
            attack_playbook=json.loads((pack_dir / "attack_playbook.json").read_text(encoding="utf-8")),
            benign_playbook=json.loads((pack_dir / "benign_playbook.json").read_text(encoding="utf-8")),
            kb_dir=kb_dir,
        )

    @property
    def display_name(self) -> str:
        return self.agent_profile.get("display_name", self.pack_id)

    def validate(self) -> list[str]:
        errors: list[str] = []
        regions = self.agent_profile.get("sensitive_regions", {})
        if len(regions) < 4:
            errors.append("agent_profile needs at least 4 sensitive_regions")
        examples = self.agent_profile.get("allowed_intent_examples", [])
        if len(examples) < 7:
            errors.append("agent_profile needs at least 7 allowed_intent_examples")
        secrets = self.secrets_vault.get("secrets", {})
        for key in ("gateway_token", "break_glass_pin", "webhook_signing_secret"):
            if key not in secrets:
                errors.append(f"secrets_vault missing {key}")
        if len(self.attack_playbook.get("scenarios", [])) < 3:
            errors.append("attack_playbook needs at least 3 scenarios")
        return errors


def playbook_for_mode(pack: DemoPack, mode: str) -> dict:
    return pack.benign_playbook if mode == "benign" else pack.attack_playbook


def playbook_choices(pack: DemoPack, mode: str) -> list[tuple[str, str]]:
    book = playbook_for_mode(pack, mode)
    return [(s["name"], s["id"]) for s in book.get("scenarios", [])]


def get_playbook_scenario(pack: DemoPack, mode: str, scenario_id: str) -> dict | None:
    for scenario in playbook_for_mode(pack, mode).get("scenarios", []):
        if scenario["id"] == scenario_id:
            return scenario
    return None


def nexa_summary_markdown(pack: DemoPack) -> str:
    org = pack.agent_profile.get("organization", "NexaCorp")
    role = pack.agent_profile.get("role", "IT support assistant")
    return (
        f"### {pack.display_name}\n"
        f"**{org}** — {role}\n\n"
        "Nexa Copilot conoce políticas, tickets y credenciales break-glass **simuladas**. "
        "Prueba un flujo normal o un ataque gradual; el panel muestra cómo MTGuard detecta "
        "el acercamiento antes del exfil."
    )
