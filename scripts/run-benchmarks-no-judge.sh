#!/usr/bin/env bash
# Run attack-scenario benchmarks WITHOUT the EscalationJudge (offline, fast).
# Validates expect_min_verdict for crescendo, salami, jailbreak.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Attack benchmarks (offline, judge OFF)…"
uv_run Mudette-scenario --all "$@"
status=$?
if [[ $status -eq 0 ]]; then
  echo "==> All benchmarks PASSED"
else
  echo "==> Some benchmarks FAILED (exit $status)" >&2
fi
exit $status
