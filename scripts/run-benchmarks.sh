#!/usr/bin/env bash
# Run all attack-playbook benchmarks (judge OFF; requires MAIN_API_KEY).
# Alias for run-benchmarks-no-judge.sh.
set -euo pipefail
exec "$(dirname "$0")/run-benchmarks-no-judge.sh" "$@"
