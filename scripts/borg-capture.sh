#!/bin/bash
# borg-capture.sh — Post-session hook for Claude Code
# Captures the most recent Claude Code session as a Borg episode.
#
# Install: Add to ~/.claude/settings.json:
# {
#   "hooks": {
#     "PostSession": [{
#       "matcher": "",
#       "command": "/Users/benj8956/Documents/Borg/scripts/borg-capture.sh"
#     }]
#   }
# }
#
# Also add to ~/.claude/settings.json to prevent session deletion:
# {
#   "history": {
#     "maxAge": "100000d"
#   }
# }

set -euo pipefail

BORG_URL="${BORG_URL:-http://localhost:8080}"
NAMESPACE="${BORG_NAMESPACE:-default}"
CLAUDE_PROJECTS_DIR="${HOME}/.claude/projects"
MIN_MESSAGES=4

# Find the most recently modified JSONL session file
LATEST=$(find "$CLAUDE_PROJECTS_DIR" -name "*.jsonl" -type f -print0 \
  | xargs -0 ls -t 2>/dev/null \
  | head -1)

if [ -z "$LATEST" ]; then
  echo "[borg-capture] No session files found in $CLAUDE_PROJECTS_DIR"
  exit 0
fi

# Extract session content: user and assistant messages
CONTENT=$(python3 -c "
import json, sys

messages = []
session_id = None
project_dir = None

with open('$LATEST') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not session_id:
            session_id = entry.get('sessionId', '')
        if not project_dir:
            project_dir = entry.get('cwd', '')

        msg = entry.get('message', {})
        role = msg.get('role', '')
        
        if role == 'user':
            content = msg.get('content', '')
            if isinstance(content, list):
                content = ' '.join(
                    p.get('text', '') if isinstance(p, dict) else str(p)
                    for p in content
                )
            if content.strip():
                messages.append(f'User: {content.strip()[:2000]}')
        elif role == 'assistant':
            content_parts = msg.get('content', [])
            if isinstance(content_parts, str):
                text = content_parts
            elif isinstance(content_parts, list):
                text = ' '.join(
                    p.get('text', '') if isinstance(p, dict) else ''
                    for p in content_parts
                    if isinstance(p, dict) and p.get('type') == 'text'
                )
            else:
                text = ''
            if text.strip():
                messages.append(f'Claude: {text.strip()[:2000]}')

if len(messages) < $MIN_MESSAGES:
    sys.exit(0)

# Truncate to last 20 messages to keep episode reasonable
output = '\n\n'.join(messages[-20:])
print(output)
" 2>/dev/null)

if [ -z "$CONTENT" ]; then
  exit 0
fi

# Detect namespace from project directory
PROJECT_DIR=$(python3 -c "
import json
with open('$LATEST') as f:
    for line in f:
        try:
            entry = json.loads(line.strip())
            cwd = entry.get('cwd', '')
            if cwd:
                print(cwd)
                break
        except:
            pass
" 2>/dev/null)

# Map project directories to namespaces
if echo "$PROJECT_DIR" | grep -qi "borg"; then
  NAMESPACE="borg"
elif echo "$PROJECT_DIR" | grep -qi "sentinel"; then
  NAMESPACE="project-sentinel"
else
  NAMESPACE="${BORG_NAMESPACE:-azure-msp}"
fi

SESSION_ID=$(basename "$LATEST" .jsonl)

# Send to Borg
curl -s -X POST "${BORG_URL}/api/learn" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
    'content': sys.stdin.read(),
    'source': 'claude-code',
    'source_id': '$SESSION_ID',
    'source_event_id': 'claude-code-$SESSION_ID',
    'namespace': '$NAMESPACE',
    'metadata': {
        'project_dir': '$PROJECT_DIR',
        'session_id': '$SESSION_ID',
        'auto_captured': True,
    },
    'participants': ['user', 'claude-code'],
}))
" <<< "$CONTENT")" > /dev/null 2>&1

echo "[borg-capture] Ingested session $SESSION_ID into namespace $NAMESPACE"
