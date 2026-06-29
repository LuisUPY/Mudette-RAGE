#!/usr/bin/env bash
# Launch the Mudette web demo (Gradio) at http://localhost:7860
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Starting Mudette demo on http://localhost:7860"
echo "    Use Ctrl+C to stop."
uv_run Mudette-demo
