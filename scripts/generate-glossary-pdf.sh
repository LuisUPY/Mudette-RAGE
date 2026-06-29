#!/usr/bin/env bash
# Generate the visual command glossary PDF (docs/Mudette-Command-Glossary.pdf)
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Generating command glossary PDF…"
uv_run python scripts/generate_command_glossary.py
echo "==> Open docs/Mudette-Command-Glossary.pdf"
