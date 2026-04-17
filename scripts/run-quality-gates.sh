#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RUFF_BIN="${RUFF_BIN:-}"
if [[ -z "$RUFF_BIN" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/ruff" ]]; then
    RUFF_BIN="$ROOT_DIR/.venv/bin/ruff"
  else
    RUFF_BIN="ruff"
  fi
fi

MODE="${1:-}"
files=()

if [[ "$MODE" == "--all" ]]; then
  while IFS= read -r file; do
    files+=("$file")
  done < <(rg --files src tests -g '*.py')
else
  while IFS= read -r file; do
    files+=("$file")
  done < <(git diff --cached --name-only --diff-filter=ACMR | rg '\.py$' || true)
fi

if [[ "${#files[@]}" -eq 0 ]]; then
  echo "[quality-gates] No staged Python files."
  exit 0
fi

echo "[quality-gates] Ruff lint with fixes"
"$RUFF_BIN" check --fix "${files[@]}"

echo "[quality-gates] Ruff format"
"$RUFF_BIN" format "${files[@]}"

if [[ "$MODE" != "--all" ]]; then
  git add -- "${files[@]}"
fi

echo "[quality-gates] Ruff final verification"
"$RUFF_BIN" check "${files[@]}"
