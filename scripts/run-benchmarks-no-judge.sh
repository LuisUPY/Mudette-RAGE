#!/usr/bin/env bash
# Run attack-scenario benchmarks WITHOUT the EscalationJudge (requires MAIN_API_KEY).
# Validates expect_min_verdict for crescendo, salami, jailbreak.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

require_env MAIN_API_KEY "Set MAIN_API_KEY or pass --main-api-key to Mudette-scenario"

echo "==> Attack benchmarks (judge OFF, API agent ON)…"
uv_run Mudette-scenario --all "$@"
status=$?
if [[ $status -eq 0 ]]; then
  echo "==> All benchmarks PASSED"
else
  echo "==> Some benchmarks FAILED (exit $status)" >&2
fi
exit $status
