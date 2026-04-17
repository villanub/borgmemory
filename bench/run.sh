#!/usr/bin/env bash
# Borg benchmark runner — executes the full suite against a local Borg engine.
#
# Usage:
#   ./bench/run.sh                      # Full A/B/C run
#   ./bench/run.sh --condition C        # Condition C only
#   ./bench/run.sh --task task-01       # Single task
#   ./bench/run.sh --report             # Regenerate latest report only
#
# Prerequisites:
#   - Docker stack running:  docker compose up -d
#   - .venv activated or run from repo root
#   - OPENAI_API_KEY set in .env

set -euo pipefail
cd "$(dirname "$0")/.."

# Load .env
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

# Activate venv if not already active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  source .venv/bin/activate
fi

# Connectivity check (skip for --report since it doesn't hit the engine)
if [[ "${1:-}" != "--report" ]]; then
  STATUS=$(curl -sf "${BORG_PUBLIC_BASE_URL:-http://localhost:8080}/health" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" \
    2>/dev/null || echo "unreachable")
  if [[ "$STATUS" != "ok" ]]; then
    echo "ERROR: Borg engine not reachable at ${BORG_PUBLIC_BASE_URL:-http://localhost:8080}"
    echo "Start it with: docker compose up -d"
    exit 1
  fi
  echo "Borg engine: $STATUS"
  echo ""
fi

python -m bench.runner "$@"
