#!/usr/bin/env bash
# Rebuild the Nexa Copilot FAISS knowledge base from demo_pack/kb_src/*.md
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Building knowledge base (FAISS + chunks)…"
uv_run python scripts/build_kb.py
echo "==> KB written to demo_pack/nexa_copilot/kb/"
