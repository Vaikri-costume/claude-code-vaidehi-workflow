#!/usr/bin/env python3
"""
Hook-Config Bootstrapper (global, SessionStart)

Fires on SessionStart (matcher: startup|resume). If the current project has no
`.claude/claude-hooks-config.json` AND no `.claude/no-claude-hooks` sentinel,
prints a directive to Claude (via stdout) suggesting `/configure-hooks` for
guided setup.

Idempotency: once the user either configures hooks (creates the config file)
or declines (creates the sentinel), this hook no-ops silently.

Hook Event: SessionStart (matcher: "startup|resume")
Always exits 0 (fail-open).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
NC = "\033[0m"

CONFIG_PATH = ".claude/claude-hooks-config.json"
SENTINEL_PATH = ".claude/no-claude-hooks"


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        hook_input = {}

    source = hook_input.get("source", "")
    if source not in ("startup", "resume"):
        return 0

    project_dir_str = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir_str:
        return 0
    project_dir = Path(project_dir_str)

    config_file = project_dir / CONFIG_PATH
    sentinel_file = project_dir / SENTINEL_PATH

    if config_file.is_file():
        return 0
    if sentinel_file.is_file():
        return 0

    message = f"""
{CYAN}[Claude Hooks — Project Setup]{NC}

This project has no Claude hooks configuration at {GREEN}.claude/claude-hooks-config.json{NC}.

Claude hooks add lightweight behaviour to this project:
  • Session-log enforcement (remind to update logs)
  • File protection (block edits to specified paths)
  • Schema verification (remind to verify after writes to specified files)
  • Phase-state capture (preserved across context compaction)

{YELLOW}Options:{NC}
  1. {GREEN}/configure-hooks{NC} — guided setup; writes the config file.
  2. {GREEN}touch .claude/no-claude-hooks{NC} — permanently skip this prompt for this project.
  3. Just continue working — no hooks fire; this reminder appears next session.
"""
    print(message)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
