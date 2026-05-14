#!/usr/bin/env python3
"""
Verification Reminder Hook (global, config-driven)

Reads `.claude/claude-hooks-config.json`:
  verify.rules: [{ glob, action }, ...]
  verify.skipDirs: [substring patterns to skip]
  verify.skipExtensions: [extension patterns to skip]

Behaviour:
  - No config or empty verify section → no-op.
  - File matches a skip rule → no-op.
  - File matches a verify rule → print reminder (60s per-file throttle).

Hook Event: PostToolUse (matcher: "Write|Edit")
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
import time
from pathlib import Path

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
NC = "\033[0m"

CONFIG_PATH = ".claude/claude-hooks-config.json"


def read_config(project_dir: Path) -> dict:
    cfg = project_dir / CONFIG_PATH
    if not cfg.is_file():
        return {}
    try:
        return json.loads(cfg.read_text())
    except (json.JSONDecodeError, IOError) as e:
        print(f"verify-reminder: ignoring malformed config: {e}", file=sys.stderr)
        return {}


def get_session_dir() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        return Path.home() / ".claude" / "sessions" / "default"
    project_hash = hashlib.md5(project_dir.encode()).hexdigest()[:8]
    session_dir = Path.home() / ".claude" / "sessions" / project_hash
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def should_skip(file_path: str, skip_dirs: list, skip_extensions: list) -> bool:
    path = Path(file_path)
    if path.suffix.lower() in skip_extensions:
        return True
    for skip_dir in skip_dirs:
        if skip_dir in file_path:
            return True
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    return False


def project_relative(file_path: str, project_dir: Path) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(project_dir.resolve()))
    except ValueError:
        return file_path


def needs_verification(rel_path: str, rules: list) -> tuple[bool, str]:
    rel_path = rel_path.replace("\\", "/")
    for rule in rules:
        pattern = rule.get("glob", "")
        action = rule.get("action", "")
        if pattern and _glob_match(rel_path, pattern):
            return True, action
    return False, ""


def _glob_match(path: str, pattern: str) -> bool:
    """Glob match with ** support across path separators."""
    if "**" not in pattern:
        return fnmatch.fnmatchcase(path, pattern)
    parts = pattern.split("**")
    cursor = 0
    for j, part in enumerate(parts):
        part = part.strip("/")
        if not part:
            continue
        if j == 0:
            if not _head_match(path, part):
                return False
            cursor = _head_match_end(path, part)
        else:
            tail = path[cursor:]
            idx = _find_glob(tail, part)
            if idx < 0:
                return False
            cursor += idx + len(part)
    return True


def _head_match(path: str, segment: str) -> bool:
    n = segment.count("/") + 1
    head = path.split("/", n)[:n]
    return fnmatch.fnmatchcase("/".join(head), segment)


def _head_match_end(path: str, segment: str) -> int:
    n = segment.count("/") + 1
    head = path.split("/", n)[:n]
    return len("/".join(head))


def _find_glob(text: str, segment: str) -> int:
    for start in range(len(text) - len(segment) + 1):
        sub = text[start : start + len(segment)]
        if fnmatch.fnmatchcase(sub, segment):
            return start
    return -1


def was_recently_reminded(file_path: str) -> bool:
    cache_file = get_session_dir() / "verify-reminder-cache.json"
    try:
        cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    except (json.JSONDecodeError, IOError):
        cache = {}
    last_reminder = cache.get(file_path, 0)
    now = time.time()
    cache[file_path] = now
    cache = {k: v for k, v in cache.items() if now - v < 300}
    try:
        cache_file.write_text(json.dumps(cache))
    except IOError:
        pass
    return (now - last_reminder) < 60


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0

    project_dir_str = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir_str:
        return 0
    project_dir = Path(project_dir_str)

    config = read_config(project_dir)
    verify_section = config.get("verify") or {}
    rules = verify_section.get("rules", [])
    if not rules:
        return 0

    skip_dirs = verify_section.get("skipDirs", [])
    skip_extensions = verify_section.get("skipExtensions", [])
    if should_skip(file_path, skip_dirs, skip_extensions):
        return 0

    rel = project_relative(file_path, project_dir)
    needs_verify, action = needs_verification(rel, rules)
    if not needs_verify:
        return 0

    if was_recently_reminded(file_path):
        return 0

    filename = Path(file_path).name
    print(f"\n{CYAN}📋 Verification reminder:{NC} {filename}\n   → {GREEN}{action}{NC}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
