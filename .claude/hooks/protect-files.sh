#!/bin/bash
# File-protection hook (global, config-driven)
#
# Reads $CLAUDE_PROJECT_DIR/.claude/claude-hooks-config.json:
#   .protect.substrings[] — path-substring patterns to block
#   .protect.basenames[]  — exact-basename patterns to block
#
# Behaviour:
#   - No config file → exit 0 (allow all edits, no protection).
#   - Config exists but no .protect section → exit 0.
#   - Match found → exit 2 with stderr message naming the file and override path.
#   - No match → exit 0.

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
FILE=""

if [ "$TOOL" = "Edit" ] || [ "$TOOL" = "Write" ]; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
fi

if [ -z "$FILE" ]; then
  exit 0
fi

CONFIG="$CLAUDE_PROJECT_DIR/.claude/claude-hooks-config.json"
if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Path-substring patterns
while IFS= read -r PATTERN; do
  if [ -n "$PATTERN" ] && [[ "$FILE" == *"$PATTERN"* ]]; then
    echo "Protected path: $FILE (matched substring '$PATTERN'). To change protection, run /configure-hooks." >&2
    exit 2
  fi
done < <(jq -r '.protect.substrings[]?' "$CONFIG" 2>/dev/null)

# Basename patterns
BASENAME=$(basename "$FILE")
while IFS= read -r PATTERN; do
  if [ -n "$PATTERN" ] && [[ "$BASENAME" == "$PATTERN" ]]; then
    echo "Protected file: $BASENAME. To change protection, run /configure-hooks." >&2
    exit 2
  fi
done < <(jq -r '.protect.basenames[]?' "$CONFIG" 2>/dev/null)

exit 0
