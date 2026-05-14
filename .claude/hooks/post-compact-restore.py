#!/usr/bin/env python3
"""
Post-Compact Context Restoration Hook — CCVW adaptation

Fires after compaction (SessionStart with source="compact") to restore context.
CCVW changes from CCMW source:
  - Session log path: memory/staging/session-log-*.md (not quality_reports/session_logs/)
  - Plan path: ~/.claude/plans/ (Claude Code plan mode, not quality_reports/plans/)
  - Added: skill run detection — scans session log for incomplete skill runs

Hook Event: SessionStart (matcher: "compact|resume")
Returns: Exit code 0 (output to stdout)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
NC = "\033[0m"


def get_session_dir() -> Path:
    """Get the session directory for storing pre-compact state."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return Path.home() / ".claude" / "sessions" / "default"

    import hashlib
    project_hash = hashlib.md5(project_dir.encode()).hexdigest()[:8]
    session_dir = Path.home() / ".claude" / "sessions" / project_hash
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def read_pre_compact_state() -> dict | None:
    """Read and delete the pre-compact state file."""
    session_dir = get_session_dir()
    state_file = session_dir / "pre-compact-state.json"

    if not state_file.exists():
        return None

    try:
        state = json.loads(state_file.read_text())
        state_file.unlink()
        return state
    except (json.JSONDecodeError, IOError):
        return None


def find_active_plan() -> dict | None:
    """Find the most recent Claude Code plan file (~/.claude/plans/)."""
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.exists():
        return None

    plan_files = sorted(plans_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not plan_files:
        return None

    latest_plan = plan_files[0]
    try:
        content = latest_plan.read_text()
    except IOError:
        return None

    status = "unknown"
    if "COMPLETED" in content.upper():
        status = "completed"
    elif "APPROVED" in content.upper():
        status = "in_progress"
    elif "DRAFT" in content.upper():
        status = "draft"

    current_task = None
    for line in content.split("\n"):
        if "- [ ]" in line:
            current_task = line.replace("- [ ]", "").strip()
            break

    return {
        "plan_path": str(latest_plan),
        "plan_name": latest_plan.name,
        "status": status,
        "current_task": current_task,
    }


def find_recent_session_log(project_dir: str) -> Path | None:
    """Find the most recent CCVW session log at memory/staging/session-log-*.md."""
    staging_dir = Path(project_dir) / "memory" / "staging"
    if not staging_dir.exists():
        return None

    log_files = sorted(
        staging_dir.glob("session-log-*.md"),
        key=lambda f: f.name,
        reverse=True,
    )
    return log_files[0] if log_files else None


def find_incomplete_skill_runs(log_path: Path) -> list[dict]:
    """
    Scan the session log for skill runs that have STEP:start but no
    matching STEP:complete or STEP:abort for the same RUN:[id].

    Returns a list of dicts: {skill, run_id, agents}
    """
    try:
        content = log_path.read_text()
    except IOError:
        return []

    # Parse all signed log entries
    # Format: **[HH:MM:SS] SKILL:[name] RUN:[id] STEP:[name]** — [event]
    entry_re = re.compile(
        r"\*\*\[[\d:]+\] SKILL:(\S+) RUN:(\S+) STEP:(\S+)\*\*\s*—\s*(.*)"
    )

    starts: dict[str, str] = {}      # run_id -> skill_name
    terminals: set[str] = set()      # run_ids with complete or abort
    agents_by_run: dict[str, list[str]] = {}  # run_id -> [agent descriptions]

    for line in content.splitlines():
        m = entry_re.search(line)
        if not m:
            continue
        skill, run_id, step, event = m.group(1), m.group(2), m.group(3), m.group(4)

        if step == "start":
            starts[run_id] = skill
        elif step in ("complete", "abort", "calibration-skipped"):
            terminals.add(run_id)
        elif step.startswith("dispatch"):
            # Collect agent description strings from the event text
            # Event contains comma-separated descriptions like: AIQuant-id, AIPatterns-id, ...
            if run_id not in agents_by_run:
                agents_by_run[run_id] = []
            # Extract agent tokens: sequences of non-space chars containing a hyphen
            agent_tokens = re.findall(r'\b[A-Za-z][A-Za-z0-9]+-[A-Za-z0-9-]+\b', event)
            agents_by_run[run_id].extend(agent_tokens)

    incomplete = []
    for run_id, skill_name in starts.items():
        if run_id not in terminals:
            agents = list(dict.fromkeys(agents_by_run.get(run_id, [])))  # deduplicate, preserve order
            incomplete.append({
                "skill": skill_name,
                "run_id": run_id,
                "agents": agents,
            })

    return incomplete


def format_restoration_message(
    pre_compact_state: dict | None,
    plan_info: dict | None,
    session_log_path: Path | None,
    incomplete_runs: list[dict],
) -> str:
    lines = []
    lines.append(f"\n{CYAN}[Context Restored After Compaction]{NC}\n")

    if pre_compact_state:
        lines.append(f"{GREEN}Pre-Compaction State:{NC}")
        if pre_compact_state.get("plan_name"):
            lines.append(f"  Plan: {pre_compact_state['plan_name']}")
            if pre_compact_state.get("current_task"):
                lines.append(f"  Next task: {pre_compact_state['current_task']}")
        if pre_compact_state.get("phase_status"):
            lines.append(f"  Phase: {pre_compact_state['phase_status']}")
            if pre_compact_state.get("phase_state_filename"):
                lines.append(f"  Phase-state source: {pre_compact_state['phase_state_filename']}")
        if pre_compact_state.get("decisions"):
            lines.append("  Recent decisions:")
            for d in pre_compact_state["decisions"][-3:]:
                lines.append(f"    - {d}")
        lines.append("")

    if session_log_path:
        lines.append(f"{GREEN}Session Log:{NC}")
        lines.append(f"  Path: {session_log_path}")
        lines.append("")

    lines.append(f"{GREEN}Logging Protocol:{NC}")
    lines.append("  Session logging protocol (three triggers):")
    lines.append("  1. Post-plan: after plan approval, capture goal/approach/rationale.")
    lines.append("  2. Incremental: append 1-3 lines on decisions, fixes, corrections, approach changes. Do not batch.")
    lines.append("  3. End-of-session: summary, open questions, blockers.")
    lines.append("  Location: quality_reports/session_logs/YYYY-MM-DD_*.md (or memory/staging/session-log-*.md for Logseq graph).")
    lines.append("")

    if incomplete_runs:
        lines.append(f"{YELLOW}Incomplete Skill Runs Detected:{NC}")
        for run in incomplete_runs:
            agents_str = ", ".join(run["agents"]) if run["agents"] else "no agents logged"
            lines.append(f"  SKILL:{run['skill']} RUN:{run['run_id']} was in progress at last session end.")
            lines.append(f"    Agents dispatched: {agents_str}")
            lines.append(f"    Re-run the skill or paste agent outputs manually to continue.")
        lines.append("")

    lines.append(f"{YELLOW}Recovery Actions:{NC}")
    lines.append("  1. Read the active plan (if any) to understand current objectives.")
    lines.append("  2. Check git status/diff for uncommitted changes.")
    lines.append("  3. Append an incremental log entry noting the compaction and current step.")
    lines.append("  4. Continue from where you left off.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        hook_input = {}

    session_source = hook_input.get("source", "")
    if session_source not in ("compact", "resume"):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return 0

    pre_compact_state = read_pre_compact_state()
    plan_info = find_active_plan()
    session_log_path = find_recent_session_log(project_dir)
    incomplete_runs = find_incomplete_skill_runs(session_log_path) if session_log_path else []

    if pre_compact_state or plan_info or session_log_path or incomplete_runs:
        message = format_restoration_message(
            pre_compact_state, plan_info, session_log_path, incomplete_runs
        )
        print(message)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
