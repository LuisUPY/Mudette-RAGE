#!/usr/bin/env bash
# Shared helpers for Mudette shell scripts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

uv_run() {
  if command -v uv >/dev/null 2>&1; then
    uv run "$@"
  else
    echo "Error: uv is required. Install from https://docs.astral.sh/uv/" >&2
    exit 1
  fi
}

require_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required. Install from https://docs.astral.sh/uv/" >&2
    exit 1
  fi
}

require_env() {
  local name="$1"
  local hint="${2:-}"
  if [[ -z "${!name:-}" ]]; then
    echo "Error: $name is required." >&2
    [[ -n "$hint" ]] && echo "  $hint" >&2
    exit 1
  fi
}
