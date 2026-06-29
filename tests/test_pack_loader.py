"""Tests for DemoPack loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from mtguard.pack_loader import REQUIRED_FILES, DemoPack, get_playbook_scenario, playbook_choices

ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "demo_pack" / "nexa_copilot"


class TestPackLoader:
    def test_load_nexa_copilot(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        assert pack.display_name == "Nexa Copilot"
        assert pack.pack_dir == PACK_DIR.resolve()

    def test_required_files_exist(self) -> None:
        for name in REQUIRED_FILES:
            assert (PACK_DIR / name).exists(), name

    def test_agent_profile_regions(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        regions = pack.agent_profile["sensitive_regions"]
        assert set(regions) >= {"credentials", "system_internals", "bulk_pii", "policy_bypass"}

    def test_secrets_vault_simulated(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        secrets = pack.secrets_vault["secrets"]
        assert secrets["gateway_token"] == "GW-7k9mN2pQ8xR4vL6w"
        assert secrets["break_glass_pin"] == "8842"

    def test_playbooks_loaded(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        assert len(pack.attack_playbook["scenarios"]) == 3
        assert len(pack.benign_playbook["scenarios"]) >= 2

    def test_validate_passes(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        assert pack.validate() == []

    def test_missing_pack_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            DemoPack.load(ROOT / "nonexistent_pack")

    def test_playbook_choices_benign(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        choices = playbook_choices(pack, "benign")
        assert len(choices) >= 2
        assert choices[0][1] == "ticket_status"

    def test_playbook_choices_redteam(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        choices = playbook_choices(pack, "redteam")
        assert any(c[1] == "crescendo_credentials" for c in choices)

    def test_get_playbook_scenario(self) -> None:
        pack = DemoPack.load(PACK_DIR)
        scenario = get_playbook_scenario(pack, "redteam", "jailbreak_direct")
        assert scenario is not None
        assert len(scenario["turns"]) == 1
