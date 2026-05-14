#!/usr/bin/env python3
"""
Pre-Compact State Capture Hook — CCVW adaptation

Fires before context compaction to capture the current state:
  - Active plan (from ~/.claude/plans/ — Claude Code plan mode)
  - Recent decisions from the latest CCVW session log
  - Phase-state from memory/staging/ if a phase-status:: marker is present
    (constitutional-governance workflow integration)

State is written to ~/.claude/sessions/<project-hash>/pre-compact-state.json
and read by post-compact-restore.py after compaction.

Hook Event: PreCompact
Stdout: not consumed post-compaction; prints summary to stderr for user visibility.
Always exits 0 (fail-open).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
NC = "\033[0m"

# Hybrid set: canonical marker (going forward) + observed CCVW log patterns.
DECISION_PATTERNS = [
    r"\*\*Decision:\*\*",
    r"FIXED\b",
    r"\[NEW\b",
    r"dismissed\b",
    r"applied:",
    r"queued\b",
    r"Fixed via\b",
    r"needs decision\b",
    r"\bsplit\b",
    r"UNVERIFIED\b",
]


def get_session_dir() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return Path.home() / ".claude" / "sessions" / "default"
    project_hash = hashlib.md5(project_dir.encode()).hexdigest()[:8]
    session_dir = Path.home() / ".claude" / "sessions" / project_hash
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def find_latest_session_log(project_dir: str) -> Path | None:
    """CCVW: memory/staging/session-log-*.md (most recent by mtime)."""
    base = Path(project_dir) / "memory" / "staging"
    if not base.exists():
        return None
    logs = sorted(base.glob("session-log-*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def find_active_plan() -> dict | None:
    """Claude Code plan mode plans live at ~/.claude/plans/."""
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.exists():
        return None

    plan_files = sorted(plans_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not plan_files:
        return None

    latest = plan_files[0]
    try:
        content = latest.read_text()
    except IOError:
        return None

    current_task = None
    for line in content.split("\n"):
        if "- [ ]" in line:
            current_task = line.replace("- [ ]", "").strip()
            break

    return {
        "plan_path": str(latest),
        "plan_name": latest.name,
        "current_task": current_task,
    }


def find_phase_state(project_dir: str) -> dict | None:
    """
    Scan a configured directory for any file containing `phase-status::`. If
    found, capture the phase-status value and the file path. Used by the
    constitutional-governance workflow integration.

    Scan-dir comes from config.phaseState.scanDir. No config or no scanDir → skip.
    """
    cfg_path = Path(project_dir) / ".claude" / "claude-hooks-config.json"
    if not cfg_path.is_file():
        return None
    try:
        config = json.loads(cfg_path.read_text())
    except (json.JSONDecodeError, IOError):
        return None
    scan_dir_rel = (config.get("phaseState") or {}).get("scanDir")
    if not scan_dir_rel:
        return None
    staging = Path(project_dir) / scan_dir_rel
    if not staging.exists():
        return None

    # Require start-of-line (with optional leading whitespace) — Logseq property
    # convention. Avoids matching `phase-status::` inside prose or code blocks.
    phase_re = re.compile(r"^\s*phase-status::\s*(.+)$", re.MULTILINE)
    for path in sorted(staging.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            text = path.read_text()
        except IOError:
            continue
        m = phase_re.search(text)
        if m:
            return {
                "phase_status": m.group(1).strip(),
                "phase_state_file": str(path),
                "phase_state_filename": path.name,
            }
    return None


def extract_recent_decisions(log_file: Path | None, limit: int = 3) -> list[str]:
    if log_file is None or not log_file.exists():
        return []
    try:
        content = log_file.read_text()
    except IOError:
        return []

    decisions: list[str] = []
    for line in content.split("\n")[-100:]:
        stripped = line.strip()
        for pattern in DECISION_PATTERNS:
            if re.search(pattern, stripped):
                if len(stripped) > 10:
                    decisions.append(stripped[:120])
                    if len(decisions) >= limit:
                        return decisions
                break
    return decisions


def save_state(state: dict) -> None:
    state_file = get_session_dir() / "pre-compact-state.json"
    state["timestamp"] = datetime.now().isoformat()
    try:
        state_file.write_text(json.dumps(state, indent=2))
    except IOError as e:
        print(f"Warning: could not save pre-compact state: {e}", file=sys.stderr)


def append_compaction_marker(log_file: Path | None, trigger: str) -> None:
    if log_file is None:
        return
    try:
        with open(log_file, "a") as f:
            f.write("\n\n---\n")
            f.write(f"**Context compaction ({trigger}) at {datetime.now().strftime('%Y-%m-%d %H:%M')}**\n")
            f.write("Check git log and ~/.claude/plans/ for current state.\n")
    except IOError:
        pass


def format_message(
    plan_info: dict | None,
    decisions: list[str],
    log_file: Path | None,
    phase_state: dict | None,
) -> str:
    lines = [f"\n{YELLOW}⚡ Context compaction starting{NC}", ""]
    if plan_info:
        lines.append(f"{GREEN}Plan captured:{NC} {plan_info['plan_name']}")
        if plan_info.get("current_task"):
            lines.append(f"  Next task: {plan_info['current_task']}")
    if log_file:
        lines.append(f"{GREEN}Session log:{NC} {log_file.name}")
    if phase_state:
        lines.append(f"{GREEN}Phase state:{NC} {phase_state['phase_status']}")
        lines.append(f"  Source: {phase_state['phase_state_filename']}")
    if decisions:
        lines.append("")
        lines.append(f"{GREEN}Recent decisions captured:{NC}")
        for d in decisions:
            lines.append(f"  • {d[:80]}")
    lines.append("")
    lines.append(f"{CYAN}State will be restored after compaction.{NC}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        hook_input = {}

    trigger = hook_input.get("trigger", "auto")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0

    log_file = find_latest_session_log(project_dir)
    plan_info = find_active_plan()
    decisions = extract_recent_decisions(log_file)
    phase_state = find_phase_state(project_dir)

    state = {
        "trigger": trigger,
        "project_dir": project_dir,
        "plan_path": plan_info["plan_path"] if plan_info else None,
        "plan_name": plan_info["plan_name"] if plan_info else None,
        "current_task": plan_info.get("current_task") if plan_info else None,
        "session_log_path": str(log_file) if log_file else None,
        "session_log_name": log_file.name if log_file else None,
        "decisions": decisions,
        "phase_status": phase_state["phase_status"] if phase_state else None,
        "phase_state_file": phase_state["phase_state_file"] if phase_state else None,
        "phase_state_filename": phase_state["phase_state_filename"] if phase_state else None,
    }

    save_state(state)
    append_compaction_marker(log_file, trigger)
    print(format_message(plan_info, decisions, log_file, phase_state), file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
