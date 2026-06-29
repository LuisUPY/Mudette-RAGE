#!/usr/bin/env bash
# Quick CI check: benign corpus must never trigger CONTAIN.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

echo "==> Benign corpus check (no CONTAIN)…"
uv_run pytest -v \
  tests/test_fusion.py::TestIntegrationFusion::test_benign_corpus_never_contain \
  tests/test_pipeline.py::TestPipelineVerdicts::test_benign_never_contain \
  tests/test_agent.py::TestMTGuardSession::test_benign_corpus_no_contain \
  "$@"
