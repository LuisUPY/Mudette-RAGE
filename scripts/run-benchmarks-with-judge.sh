#!/usr/bin/env bash
# Run attack benchmarks WITH EscalationJudge (requires JUDGE_API_KEY in env).
# Optional: MAIN_API_KEY for online Nexa responses (defense metrics still primary).
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

if [[ -z "${JUDGE_API_KEY:-}" ]]; then
  echo "Error: set JUDGE_API_KEY before running benchmarks with judge." >&2
  echo "  export JUDGE_API_KEY='sk-…'   # lightweight model (gpt-4o-mini)" >&2
  exit 1
fi

ARGS=(--all --judge --judge-api-key "$JUDGE_API_KEY")
if [[ -n "${MAIN_API_KEY:-}" ]]; then
  ARGS+=(--main-api-key "$MAIN_API_KEY")
  echo "==> Attack benchmarks (judge ON, agent online)…"
else
  echo "==> Attack benchmarks (judge ON, agent offline RAG)…"
fi

uv_run Mudette-scenario "${ARGS[@]}" "$@"
status=$?
[[ $status -eq 0 ]] && echo "==> All benchmarks PASSED" || echo "==> FAILED (exit $status)" >&2
exit $status
