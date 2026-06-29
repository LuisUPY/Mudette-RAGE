#!/usr/bin/env bash
# Run attack benchmarks WITH EscalationJudge (requires MAIN_API_KEY + JUDGE_API_KEY).
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

require_env MAIN_API_KEY "export MAIN_API_KEY='nvapi-…'   # Nexa Copilot (llama-3.3-70b)"
require_env JUDGE_API_KEY "export JUDGE_API_KEY='nvapi-…'   # EscalationJudge (llama-3.1-8b)"

echo "==> Attack benchmarks (judge ON, agent API ON)…"
uv_run Mudette-scenario --all --judge \
  --main-api-key "$MAIN_API_KEY" \
  --judge-api-key "$JUDGE_API_KEY" \
  "$@"
status=$?
[[ $status -eq 0 ]] && echo "==> All benchmarks PASSED" || echo "==> FAILED (exit $status)" >&2
exit $status
