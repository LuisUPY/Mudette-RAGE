#!/usr/bin/env bash
# Run all attack-playbook benchmarks (offline defense pipeline).
# Alias for run-benchmarks-no-judge.sh — no API keys needed.
set -euo pipefail
exec "$(dirname "$0")/run-benchmarks-no-judge.sh" "$@"
