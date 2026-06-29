#!/usr/bin/env bash
# Run a single playbook scenario by ID.
# Usage: ./scripts/run-scenario.sh crescendo_credentials
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

SCENARIO="${1:-}"
if [[ -z "$SCENARIO" ]]; then
  echo "Usage: $0 <scenario_id>" >&2
  echo "Examples: crescendo_credentials | salami_export | jailbreak_direct | ticket_status" >&2
  exit 1
fi

shift || true
require_env MAIN_API_KEY "export MAIN_API_KEY='nvapi-…'"

echo "==> Running scenario: $SCENARIO"
uv_run Mudette-scenario --scenario "$SCENARIO" --main-api-key "$MAIN_API_KEY" "$@"
