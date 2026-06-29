"""CLI scenario runner for attack/benign playbooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mtguard.agent import MTGuardSession
from mtguard.models import Verdict
from mtguard.pack_loader import DemoPack, get_playbook_scenario, playbook_for_mode

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACK = ROOT / "demo_pack" / "nexa_copilot"

_VERDICT_RANK = {
    Verdict.CLEAR: 0,
    Verdict.WATCH: 1,
    Verdict.ALERT: 2,
    Verdict.CONTAIN: 3,
}


def verdict_meets_minimum(actual: Verdict, minimum: str) -> bool:
    return _VERDICT_RANK[actual] >= _VERDICT_RANK[Verdict(minimum)]


def run_scenario(
    pack_dir: Path,
    scenario_id: str,
    mode: str = "redteam",
    main_api_key: str | None = None,
    judge_api_key: str | None = None,
    judge_enabled: bool = False,
) -> dict:
    pack = DemoPack.load(pack_dir)
    scenario = get_playbook_scenario(pack, mode, scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    session = MTGuardSession.from_pack_dir(
        pack_dir,
        main_api_key=main_api_key,
        judge_api_key=judge_api_key,
        judge_enabled=judge_enabled and bool(judge_api_key),
    )

    turns_out: list[dict] = []
    for turn in scenario["turns"]:
        result = session.turn(turn)
        trace = result.trace.to_dict()
        turns_out.append(
            {
                "message": turn,
                "verdict": result.fusion.verdict.value,
                "risk_score": result.fusion.risk_score,
                "allow_llm": result.gate.allow_llm,
                "judge": trace.get("judge"),
            }
        )

    final = turns_out[-1]
    expect = scenario.get("expect_min_verdict")
    passed = verdict_meets_minimum(Verdict(final["verdict"]), expect) if expect else True

    return {
        "scenario_id": scenario_id,
        "name": scenario.get("name"),
        "passed": passed,
        "expect_min_verdict": expect,
        "final_verdict": final["verdict"],
        "final_risk": final["risk_score"],
        "turns": turns_out,
    }


def run_all_attack_scenarios(pack_dir: Path, **kwargs) -> list[dict]:
    pack = DemoPack.load(pack_dir)
    results = []
    for scenario in playbook_for_mode(pack, "redteam").get("scenarios", []):
        results.append(run_scenario(pack_dir, scenario["id"], mode="redteam", **kwargs))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Mudette MTGuard playbook scenarios")
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--scenario", type=str, help="Scenario id (e.g. crescendo_credentials)")
    parser.add_argument("--all", action="store_true", help="Run all attack scenarios")
    parser.add_argument("--mode", choices=["benign", "redteam"], default="redteam")
    parser.add_argument("--main-api-key", type=str, default=None, help="Main Nexa Copilot API key")
    parser.add_argument("--judge-api-key", type=str, default=None, help="Judge API key (lighter model)")
    parser.add_argument("--judge", action="store_true", help="Enable EscalationJudge")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    kwargs = {
        "main_api_key": args.main_api_key,
        "judge_api_key": args.judge_api_key,
        "judge_enabled": args.judge,
    }

    if args.all:
        results = run_all_attack_scenarios(args.pack, **kwargs)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                status = "PASS" if r["passed"] else "FAIL"
                print(
                    f"[{status}] {r['scenario_id']}: "
                    f"{r['final_verdict']} (risk {r['final_risk']}) "
                    f"expect>={r['expect_min_verdict']}"
                )
        failed = [r for r in results if not r["passed"]]
        sys.exit(1 if failed else 0)

    if not args.scenario:
        parser.error("Provide --scenario ID or --all")

    result = run_scenario(args.pack, args.scenario, mode=args.mode, **kwargs)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for i, t in enumerate(result["turns"]):
            print(f"  T{i} risk={t['risk_score']:3d} {t['verdict']:8s} | {t['message'][:60]}")
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"\n[{status}] {result['scenario_id']}: {result['final_verdict']} "
            f"(risk {result['final_risk']}) expect>={result['expect_min_verdict']}"
        )
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
