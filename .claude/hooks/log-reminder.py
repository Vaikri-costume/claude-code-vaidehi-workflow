#!/usr/bin/env python3
"""
Session Log Reminder Hook (global, config-driven)

Stop hook that prompts the user to maintain a session log. Opt-in per-project
via `.claude/claude-hooks-config.json` field `sessionLog.glob` — a glob pattern
relative to project root identifying session-log files.

Behaviour:
  - No config file → exit 0 silently (no-op).
  - Config present but no `sessionLog.glob` → exit 0 silently.
  - Glob set, no matching file → block once asking the user to create one.
  - Glob set, file exists, mtime unchanged for THRESHOLD responses → block once.
  - Glob set, file updated → reset counter.

`stop_hook_active` short-circuit prevents infinite loops.

Example CCVW config:
    "sessionLog": { "glob": "memory/staging/session-log-*.md" }
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

THRESHOLD = 15
CONFIG_PATH = ".claude/claude-hooks-config.json"


def read_config(project_dir: Path) -> dict:
    """Read project hooks config; return {} on absent or malformed."""
    cfg = project_dir / CONFIG_PATH
    if not cfg.is_file():
        return {}
    try:
        return json.loads(cfg.read_text())
    except (json.JSONDecodeError, IOError) as e:
        print(f"log-reminder: ignoring malformed config: {e}", file=sys.stderr)
        return {}


def get_state_dir() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        state_dir = Path.home() / ".claude" / "sessions" / "default"
    else:
        project_hash = hashlib.md5(project_dir.encode()).hexdigest()[:8]
        state_dir = Path.home() / ".claude" / "sessions" / project_hash
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def find_latest_log(project_dir: Path, pattern: str) -> tuple[Path | None, float]:
    try:
        matches = [p for p in project_dir.glob(pattern) if p.is_file()]
    except (ValueError, OSError):
        return None, 0.0
    if not matches:
        return None, 0.0
    latest = max(matches, key=lambda f: f.stat().st_mtime)
    return latest, latest.stat().st_mtime


def get_state_path() -> Path:
    return get_state_dir() / "log-reminder-state.json"


def load_state(state_path: Path) -> dict:
    try:
        return json.loads(state_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"counter": 0, "last_mtime": 0.0, "reminded": False, "no_log_reminded": False}


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state))


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    if hook_input.get("stop_hook_active", False):
        sys.exit(0)

    project_dir_str = hook_input.get("cwd", "") or os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir_str:
        sys.exit(0)
    project_dir = Path(project_dir_str)

    config = read_config(project_dir)
    glob_pattern = (config.get("sessionLog") or {}).get("glob")
    if not glob_pattern:
        sys.exit(0)

    state_path = get_state_path()
    state = load_state(state_path)

    latest_log, current_mtime = find_latest_log(project_dir, glob_pattern)
    today = datetime.now().strftime("%Y-%m-%d")

    # Case 1: glob set but no matching file — remind once.
    if latest_log is None:
        if not state.get("no_log_reminded", False):
            state["no_log_reminded"] = True
            save_state(state_path, state)
            output = {
                "decision": "block",
                "reason": (
                    f"No session log found matching `{glob_pattern}`. "
                    f"Create one (e.g. substitute YYYY-MM-DD with {today}) before continuing. "
                    f"To change the glob or disable this prompt, run /configure-hooks."
                ),
            }
            json.dump(output, sys.stdout)
        sys.exit(0)

    # Case 2: log updated — reset.
    if current_mtime != state["last_mtime"]:
        state = {
            "counter": 0,
            "last_mtime": current_mtime,
            "reminded": False,
            "no_log_reminded": False,
        }
        save_state(state_path, state)
        sys.exit(0)

    # Case 3: log not updated — increment.
    state["counter"] += 1

    if state["counter"] >= THRESHOLD and not state["reminded"]:
        state["reminded"] = True
        save_state(state_path, state)
        output = {
            "decision": "block",
            "reason": (
                f"SESSION LOG REMINDER: {state['counter']} responses without "
                f"updating the session log. Append your recent progress to "
                f"{latest_log.name}."
            ),
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    save_state(state_path, state)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
