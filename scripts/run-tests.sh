#!/usr/bin/env bash
# Run the full offline test suite (pytest). No API keys required.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Running pytest (offline)…"
uv_run pytest -v "$@"
