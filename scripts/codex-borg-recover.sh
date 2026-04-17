#!/usr/bin/env bash

set -euo pipefail

server="${1:-borg}"
if [[ $# -gt 0 ]]; then
  shift
fi

codex mcp login "$server"

if [[ $# -gt 0 ]]; then
  exec codex resume --last "$@"
fi

exec codex resume --last
