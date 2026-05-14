---
name: configure-hooks
description: Configure or update the Claude hooks for the current project. Writes .claude/claude-hooks-config.json with sections for session-log enforcement, file protection, schema verification, and phase-state capture. Use when the user runs /configure-hooks, when the detect-config bootstrapper directs you here, or when the user asks to "set up hooks", "change file protection", "configure session logging", or "edit hook config".
---

# Configure Claude Hooks

Drive an interactive setup conversation that writes (or updates) `.claude/claude-hooks-config.json` for the current project. Works for both initial setup and ongoing edits.

## When to invoke

- The user runs `/configure-hooks` explicitly.
- The `detect-config.py` SessionStart hook printed a setup directive on the current session.
- The user asks to add/change/remove a file protection, a verification rule, a session-log glob, or phase-state scan dir.

## Step 0: Read current state

1. Check `$CLAUDE_PROJECT_DIR/.claude/claude-hooks-config.json`. If it exists, parse it and present the current values to the user before asking what to change.
2. If config absent: announce this is initial setup.

## Step 1: Pick which concerns to enable (initial setup only)

Use AskUserQuestion with `multiSelect: true` to let the user pick from:

- **Session-log enforcement** — Stop hook reminds to update a session log every 15 responses.
- **File protection** — PreToolUse hook blocks edits to specified paths.
- **Schema verification** — PostToolUse hook reminds to verify after writes to specified files.
- **Phase-state capture** — PreCompact hook captures `phase-status::` markers for workflow continuity.

For updates: skip this step. Ask the user which existing section to change (and offer "add a new section" / "remove a section").

## Step 2: Gather config per enabled concern

For each enabled concern, use AskUserQuestion to gather specifics. Suggested defaults below; offer them as a "(Recommended)" first option, but let the user override.

### Session-log enforcement

Ask: "Where do session logs live in this project? (glob pattern relative to project root)"
- Default suggestion: `memory/staging/session-log-*.md`
- Other plausible patterns: `quality_reports/session_logs/*.md`, `docs/session-logs/*.md`

Writes to `sessionLog.glob`.

### File protection

Ask: "Which paths should be protected from edits? Two kinds:"
- **Substrings** — paths containing a given substring are blocked. Use for whole directories (`/Zotero/`, `/secrets/`) or canonical-path files (`assets/storages/.../canonical.bib`).
- **Basenames** — files with a given filename are blocked anywhere in the tree. Use for `CLAUDE.md`, `config.edn`, sensitive single-file conventions.

For each, prompt for a comma-separated list or one-at-a-time entries. Write to `protect.substrings` and `protect.basenames`.

### Schema verification

Ask: "Which file patterns trigger a verification reminder after write?"
- Each rule has a glob (e.g. `pages/**/*.md`) + an action description (e.g. "check schema X, Y, Z").
- Also ask for `skipDirs` (substring patterns to skip — e.g. `/memory/`, `/.claude/`) and `skipExtensions` (e.g. `.py`, `.bib`).

Write to `verify.rules`, `verify.skipDirs`, `verify.skipExtensions`.

### Phase-state capture

Ask: "Which directory should be scanned for `phase-status::` markers before context compaction?"
- Default: `memory/staging/`
- Other: any directory where workflow progress files live.

Write to `phaseState.scanDir`.

## Step 3: Show diff and confirm

Before writing:
1. Render the proposed new config as JSON.
2. If a previous config exists, render a clear diff (line-by-line; highlight added/removed/changed).
3. Use AskUserQuestion: "Write this config?" with options Yes / Edit one section / Cancel.

## Step 4: Write atomically

1. Write the new config to `.claude/claude-hooks-config.json.tmp`.
2. `mv .claude/claude-hooks-config.json.tmp .claude/claude-hooks-config.json` (atomic rename).
3. Confirm to the user: "Config written. Hooks will pick up the new settings on the next event fire."

## Step 5: Suggest commit

If the project is a git repo, suggest:
> "Run `git add .claude/claude-hooks-config.json && git commit -m 'Configure Claude hooks'` to commit this config alongside your project setup."

If the user wants to skip all of this in the future for this project, offer to write `.claude/no-claude-hooks` (the sentinel that silences the bootstrapper).

## Decline flow

If the user says "skip" / "not now" / "leave it" at any point:
1. Write `.claude/no-claude-hooks` with the comment `# Skip Claude hooks bootstrap prompts. Delete this file to re-enable.`
2. Confirm: "Hooks bootstrap will not prompt again for this project. Delete `.claude/no-claude-hooks` to re-enable."

## Failure modes

- **Malformed existing config** — show the user the parse error verbatim and ask whether to overwrite or fix manually.
- **Permission denied on write** — surface the OS error and suggest `chmod` or running with appropriate permissions.
- **Mid-flow abort** — leave the partial state in `.claude/claude-hooks-config.json.tmp` and announce: "Partial config saved at `.tmp`. Re-run /configure-hooks to resume."

## What this skill is NOT

- It does not install or move hook scripts. Hook scripts live at `~/.claude/hooks/` (user-global) and are managed separately.
- It does not edit `settings.json` (project or global). Hook bindings are wired in `~/.claude/settings.json` once and persist across projects.
- It does not enable or disable individual hooks. The hooks decide per-event whether to act based on their corresponding config section. A missing section means no-op, not disabled.
