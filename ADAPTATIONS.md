# ADAPTATIONS

Tracks how CCMW (Claude Code My Workflow) skills and patterns have been adapted for CCVW (Claude Code Vaidehi Workflow). Each entry describes what changed and why.

---

## Writing analysis skills

| Skill | CCMW original | CCVW adaptation | Reason |
|-------|---------------|-----------------|--------|
| proofread | Single-agent lecture-file proofreader (grammar, typos, overflow, consistency, academic register) | 12-step multi-agent pipeline: 3 paired primary agents (surface, consistency, register), two-tier canonical vocabulary check (paired Canonical-1 + paired Canonical-2 self-discovery), dual challenger pair, single presentation agent. Essay-type-routed register brief (research vs personal/application/other). | Essay writing context requires domain-aware register checking and canonical terminology management across research projects. Single agent insufficient for confidence-tagged parallel analysis. |
| plagiarism-check | n/a (new skill) | 12-step pipeline: Tier 1 dual self-discovery (Glob filter on `type:: source` + project filter) → optional cache → post-Tier-1 scope gate → Tier 2 paired per-source agents + dual structural pair + dual voice pair → cross-structural/voice merge → dual challenger → presentation. Three modes: citation-check / full-scan / voice-only. | Domain: Bollywood costume studies — foundational sources (Dwyer, Ganti, Bhabha, Said) heavily engaged; structural mirroring expected in analytical writing. Challenger adjudicates context-appropriateness of structural and voice findings against essay type and disciplinary norms. |
| ai-detection-check | n/a (new skill) | 11-step pipeline: deterministic compute_metrics.py (CV, TTR, hedge density) + find_ai_patterns.py (14 patterns) prescans → dual quant + dual pattern + dual voice/texture agents → calibration gate → cross-B/C merge → dual challenger → presentation. Strict-scope challenger (does not infer norms from training data for adjacent fields). | Academic writing in film/fashion studies has specific hedging norms and vocabulary registers (Indian fashion terminology, transliterated terms). Generic AI detection thresholds need calibration to disciplinary standards. The strict-scope challenger prevents false positives on domain-standard analytical voice. |
| review-writing | n/a (new skill) | 10-step pipeline: 4 dual domain pairs (argument structure, clarity, evidence, voice) + dual challenger + presentation. Deterministic count_citations.py prescan for research essays. Essay-type-routed evidence and voice briefs. | Research essays and personal/application essays have distinct evidence standards (citation density vs concrete specificity). Argument and voice are different concerns for analytical vs application writing. Cross-domain merge for findings flagged by multiple domain pairs. |

## Convergence methodology

The four skills passed through an iterative trace + fix loop dispatched as Explore subagents. Each skill ran forward + backward traces (per `memory/context/context-{forward,backward}-trace-prompt.md`) on the SKILL.md and supporting files. Every issue surfaced was fixed inline; the next round verified. Convergence: when a round surfaces only edge-case completeness gaps that don't risk runtime data loss.

The first two skills (proofread + ai-detection-check) ran 8 rounds each — the slow convergence yielded 23 generalisable bug-WHYs that became the cross-skill lesson catalogue. The last two (review-writing + plagiarism-check) inherited the lessons via a converged template and converged in 2 and 5 rounds respectively, validating lesson #21 (template-driven builds converge dramatically faster than from-scratch).

## Trace prompt updates

`memory/context/context-forward-trace-prompt.md` and `context-backward-trace-prompt.md` track the canonical evaluator definitions used by all trace agent dispatches. Updates over the build:
- Forward trace: agent description string consistency check, variable placeholder namespace check, mode-conditional completeness check
- Backward trace: Pass 2 step-level input check (in addition to the original Pass 1 script-output check)

---

## Hook architecture: hardcoded → config-driven (Phase 8, 2026-05-14)

| Hook | CCMW original | CCVW adaptation | Reason |
|------|---------------|-----------------|--------|
| `protect-files.sh` | Hardcoded `PROTECTED_PATTERNS` Bash array (basename match only) | Reads `protect.substrings` + `protect.basenames` from `.claude/claude-hooks-config.json`. Two match modes (substring for paths/directories, basename for filenames). | Basename match cannot distinguish canonical files from auto-generated duplicates (e.g. multiple `Zotero.bib` copies, only one canonical). Substring match handles whole-directory protection (`/Zotero/`, `/secrets/`) that basename can't. Config in JSON is editable without touching shell. |
| `verify-reminder.py` | Hardcoded `VERIFY_EXTENSIONS` dict keyed by extension (`.tex` → action) | Reads `verify.rules: [{glob, action}]` from config. Glob-based; supports `**` patterns. | Extension keying conflates all `.md` files into one rule, but real projects need path-scoped triggers (e.g. `pages/**/*.md` triggers but `memory/**/*.md` doesn't). Glob match handles this; extension match can't. |
| `log-reminder.py` | Hardcoded path `quality_reports/session_logs/*.md` | Reads `sessionLog.glob` from config. No-ops when absent. | Projects with non-CCMW conventions (e.g. Logseq graphs using `memory/staging/session-log-*.md`) need a different path. Config makes path-convention agnostic; absence makes it opt-in (so the hook installed globally won't be noisy in projects that don't track session logs). |
| `pre-compact.py` | Hardcoded `quality_reports/session_logs/` scan + CCMW decision-marker regexes (`Decision:`, `Decided:`, `Chose:`, `→`, `•`) | Reads `phaseState.scanDir` from config for phase-status capture. Decision-extraction regex broadened to a hybrid set covering both CCMW conventions and observed alternatives (`**Decision:**`, `FIXED`, `[NEW`, `dismissed`, `applied:`, etc.). | Long-running multi-phase workflows (e.g. constitutional-governance) need their phase-status captured before context compaction. Config-driven scan dir means any project with workflow state can opt in by setting one config field. Broader regex set catches decisions written in non-CCMW styles. |
| `post-compact-restore.py` | Reads pre-compact state, finds latest plan + session log | Adds: skill-run-incomplete detection (regex match for in-progress skill markers in session logs), phase-state surfacing from pre-compact-state.json, plan-info from Claude Code plan mode (`~/.claude/plans/`). | Multi-agent skills that dispatch parallel sub-agents can be mid-flight when compaction hits. The new detection surfaces incomplete runs so the user can resume them. Phase-state surfacing matches the pre-compact extension. Claude Code plan-mode plan paths are universal (not CCMW-specific). |
| `detect-config.py` | n/a (new hook) | SessionStart bootstrapper: matcher `startup\|resume`. Prompts user when config missing AND no opt-out sentinel exists. Idempotent. | New projects without explicit hook config need a low-friction setup path. Bootstrapper + `/configure-hooks` skill replaces "edit JSON by hand" with a guided AskUserQuestion flow. Sentinel-based opt-out (`.claude/no-claude-hooks`) prevents prompt fatigue. |
| `notify.sh` | OS notification | Unchanged | Fully generic; no per-project config needed. |
| `context-monitor.py` | Tool-call counting + tiered warnings | Unchanged; `MAX_TOOL_CALLS` constant calibrated up from CCMW's 150 to 200 (CCVW workflows dispatch many parallel sub-agents per phase) | Calibration constant change only; otherwise generic. |

### Why config-driven (rather than hardcoded across forks)

The CCMW template is forked into many domains (econometrics, biology, physics, costume studies, Logseq graphs). Each domain has different paths, different files to protect, different verification triggers. Hardcoded values force each fork to maintain a divergent copy of every hook script. Config-driven hooks centralise the *behaviour* in version-controlled scripts and the *paths* in a per-project JSON file. Forks share scripts via git; configs are per-project (committable alongside the project, not part of the template).

### Bootstrapper pattern

The bootstrapper hook prints a directive to Claude's stdout context on SessionStart. Claude reads it as turn-1 context and decides when to surface it to the user. The skill (`/configure-hooks`) drives the actual setup via `AskUserQuestion`. Result: the user opts in to hook setup at a natural moment, not via a forced prompt. The opt-out (`.claude/no-claude-hooks`) is a single touch-file command, documented in the bootstrapper message itself.

### Two-tier protection match (substring + basename)

CCMW's basename-only protection (`if [[ "$BASENAME" == "$PATTERN" ]]`) cannot handle:
- **Canonical files with multiple copies.** Example: Zotero auto-generates a `Zotero.bib` export in one directory while the canonical bib lives elsewhere; only the canonical should be protected.
- **Whole-directory locks.** Example: `Zotero/` (the application data dir) should be entirely read-only; basename match would have to enumerate every file inside.

The substring match handles both cases. Basename match is retained for the common case where a file's name (anywhere in the tree) is what matters (`CLAUDE.md`, `config.edn`).
