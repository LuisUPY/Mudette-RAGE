#!/usr/bin/env bash
# Run the full test suite (pytest). NVIDIA NIM calls are mocked — no real API keys needed.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Running pytest (mocked API)…"
uv_run pytest -v "$@"
