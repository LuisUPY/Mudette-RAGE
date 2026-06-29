#!/usr/bin/env bash
# Install Mudette dependencies (Python packages + dev tools for tests/PDF).
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
require_uv

echo "==> Installing Mudette dependencies…"
uv sync --group dev
echo "==> Done. Next: ./scripts/run-demo.sh or ./scripts/run-tests.sh"
