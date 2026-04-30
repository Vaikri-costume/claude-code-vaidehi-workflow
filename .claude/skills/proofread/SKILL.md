---
name: proofread
description: Use this skill whenever Vaidehi shares a draft essay, piece of writing, or any text that needs proofreading — before submission, during revision, or to catch errors. Trigger on phrases like "proofread this", "check my writing", "review for errors", "is my spelling correct", "check grammar", "British spelling", "does this read consistently", or when any draft text is pasted for review. Handles grammar, British spelling, typos, consistency, and register quality (research vs personal essay voice). Also consults and builds project-specific canonical terminology lists across runs. Works for research essays, personal statements, application essays, and any other writing.
argument-hint: "[optional: draft file path]"
---

# proofread

Proofreads a draft essay for grammar, typos, British spelling, consistency, and register quality. Three specialised agent pairs (surface, consistency, register) + two-tier canonical vocabulary check + dual challenger adjudication + presentation agent. Project-aware: builds canonical spelling lists across runs.

---

## Invocation

```
/proofread [optional: file path or pasted text]
```

---

## Execution

**Mid-cycle output rule:** Show brief dispatch signals after Steps 5, 7, 9, and 11. Allow AskUserQuestion in Steps 0, 2, 3, and 8. Do not narrate synthesis, canonical lookup details, or intermediate analysis.

**Compaction survival is mandatory.** Every step persists its outputs to disk and updates a state file at `memory/staging/proofread-state-[run-id].md`. If the conversation hits a compaction boundary mid-run, Step 0 detects the in-progress state file on the next invocation and offers the writer a choice to resume from the last completed step or start fresh. This is non-negotiable — the writer cannot afford to lose 6 primary + 2 canonical + 2 challenger + 1 presentation agent's worth of work because a context window filled at the wrong moment. See `.claude/references/compaction-survival.md` for the shared pattern that applies across all writing analysis skills.

### Step 0 — Resume check

Glob `memory/staging/proofread-state-*.md` for any state files. For each match, read its YAML frontmatter and check `status:`.

- **None found, or all `status: complete` / `status: abandoned`:** continue to Step 1 with a new run_id.
- **Exactly one with `status: in-progress`:** use AskUserQuestion: "Found an in-progress proofread run [run-id] for [draft_path] (last completed step: [last_completed_step], updated [last_updated]). Resume or start fresh?" Options: ["Resume" / "Start fresh"].
  - **Resume:** (1) load every field in the state file's frontmatter into executor context; (2) for each section under `## Step outputs` up to and including `last_completed_step`, read the referenced file paths from disk and load them into the corresponding executor variable ([PARAGRAPH_MAP], [SPELLING_PRESCAN], [CONSISTENCY_CANDIDATES], [SURFACE_FINDINGS], [CONSISTENCY_FINDINGS], [REGISTER_FINDINGS], [UNRECOGNISED_WORDS], [UNRESOLVED], [MIGRATION_FINDINGS], [STILL_UNKNOWN], [ALL_FINDINGS], [CHALLENGER_VERDICTS], coverage notes, raw agent outputs, corrected agent outputs, raw challenger outputs — whichever exist for the resume point); (3) **if `last_completed_step >= 4`, deterministically re-execute Step 4's brief-loading logic** (read `.claude/skills/proofread/references/surface.md` → [SURFACE_BRIEF]; `consistency.md` → [CONSISTENCY_BRIEF]; `register-research.md` or `register-personal.md` per `essay_type` from frontmatter → [REGISTER_BRIEF]) — briefs are not persisted to disk because they are deterministic functions of essay_type and version-controlled, but Step 5 references them verbatim if Step 5 itself is re-run on a one-failed re-dispatch path, so the resume protocol must reload them before skipping ahead. Append to session log: `**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:resume** — Resumed from step [last_completed_step]`. Skip Steps 1 through `last_completed_step` and continue from step (last_completed_step + 1).
  - **Start fresh:** rename the state file to `proofread-state-[old_run_id]-abandoned-[YYYYMMDD-HHMMSS].md` and update its frontmatter `status: abandoned`. Continue to Step 1 with a new run_id.
- **Multiple `status: in-progress` (rare; indicates prior corruption):** use AskUserQuestion to list each, let the writer pick one to resume or "Abandon all and start fresh." If "Abandon all", rename each to abandoned form. If pick one, treat the others as abandoned and resume the chosen one.

**Variable lifecycle (resume protocol — applies to all consumer steps below).** Variables produced by step N are persisted to disk via that step's State-write block. On resume, the Step 0 Resume action above is the single point that loads every persisted variable from disk into executor context — including (a) every frontmatter field (`project_name`, `project_path`, `essay_type`, `draft_path`, `filename`, `input_mode`, `canonical_status`, `briefs_loaded`), (b) every `## Step outputs` file path up to `last_completed_step`, and (c) brief content (re-read from `references/*.md` per the routing rule in Step 4 — these are deterministic and version-controlled, so re-reading on resume gives identical content). After Step 0 returns, every variable a consumer step references is in executor context. Consumer steps do NOT need per-step "Load X from disk" instructions — referring to a variable by name is sufficient. (The trace agents are right that the dependency isn't restated at every consumer site; this rule is the single source of truth that makes those restatements unnecessary.)

### Step 1 — Log start

Append to `memory/staging/session-log-[YYYY-MM-DD].md`:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:start** — Run begun.
```

The run ID is the current timestamp at second precision (e.g., `20260424-143107`). Use this same ID in all subsequent log entries and agent description strings for this run.

**Create the run-state file at `memory/staging/proofread-state-[run-id].md`** with this initial content:
```
---
run_id: [run-id]
skill: proofread
draft_path: (set in Step 3)
project_name: (set in Step 2)
project_path: (set in Step 2)
essay_type: (set in Step 2)
filename: (set in Step 3)
input_mode: (set in Step 3)
last_completed_step: 1
status: in-progress
started: [ISO timestamp now]
last_updated: [ISO timestamp now]
---

## Step outputs

### Step 1 — Log start
session_log_path: memory/staging/session-log-[YYYY-MM-DD].md
```

**State-write rule (applies to every step that follows):** at the end of each step, write any new variables produced by that step to disk under `memory/staging/proofread-[run-id]/` and append a `### Step N — [name]` section to the state file with the on-disk paths or short literal values, then update the frontmatter's `last_completed_step` and `last_updated`. The full pattern and rationale are in `.claude/references/compaction-survival.md`. Do not skip the state-write — without it, a compaction-induced resume cannot reconstruct the variable.

### Step 2 — Load context

**Project name:**
If a project name was provided at invocation: [PROJECT_NAME] = that value. Construct [PROJECT_PATH] = `memory/projects/project-[PROJECT_NAME].md`. Verify it exists (Glob). If not found: log a warning noting the project file was not found, set [PROJECT_PATH] = `memory/projects/project-general.md` and [PROJECT_NAME] = "general".

If no project name was provided at invocation: use AskUserQuestion: "Project name? (enables canonical vocabulary lookup)" Options: ["Use General project" / "I'll type it in Other"]. If user cancels: log `STEP:abort — user cancelled at project name question` and exit. If user selects "I'll type it in Other" and Other has a value: [PROJECT_NAME] = that value; construct and verify [PROJECT_PATH] as above. If "Use General project" or Other is empty: [PROJECT_NAME] = "general"; [PROJECT_PATH] = `memory/projects/project-general.md`.

If [PROJECT_PATH] = `memory/projects/project-general.md` and that file does not exist: note "project-general.md not found — canonical vocabulary unavailable this run" in [CANONICAL_STATUS] = "unavailable". Continue — do not abort. In all other cases (project file found, or project-general.md exists), [CANONICAL_STATUS] is not set. Step 7 checks for the value "unavailable" explicitly — not set = available, and the canonical check proceeds.

**Essay type:**
If essay type was provided at invocation: [type] = that value. Skip the question.

If not provided: use AskUserQuestion: "Essay type?" Options: ["research" / "personal" / "application" / "other"]. If user cancels: log `STEP:abort — user cancelled at essay type question` and exit. Store the selected value as [type].

**State-write (Step 2):** update the run-state file's frontmatter with `project_name: [PROJECT_NAME]`, `project_path: [PROJECT_PATH]`, `essay_type: [type]`, and `canonical_status: [available | unavailable]`. Update `last_completed_step: 2` and `last_updated`. Without this, a compaction-induced resume cannot reconstruct project context.

### Step 3 — Load draft

If a draft was provided at invocation:
- If it is a file path: store as [DRAFT_PATH]. Verify it exists (Glob or Read attempt). If not found: log `STEP:abort — Draft file not found: [path]` and exit. Record input mode as "file". Record [filename] as the base filename without extension (e.g., for `pages/my-draft.md`, [filename] = `my-draft`).
- If it is pasted text: save to `memory/staging/draft-[run-id].md`. Then run `python3 .claude/scripts/strip_markers.py memory/staging/draft-[run-id].md` to strip Logseq bullet markers in place (the script removes a leading `- ` from each line, leaving `---` horizontal rules untouched). Set [DRAFT_PATH] to that path. Record input mode as "paste". Record [filename] as `paste`.

If no draft was provided at invocation: use AskUserQuestion: "Paste the draft text, or provide a file path." Options: ["File path" / "Paste text"] — user enters path or text via Other. If user cancels or Other is empty: log `STEP:abort — no draft provided` and exit. Handle response as one of the two cases above.

If pasted text was used and `python3 .claude/scripts/strip_markers.py memory/staging/draft-[run-id].md` exits non-zero: log `STEP:abort — strip_markers.py failed (exit [N])` and exit. (The script's exit-1 conditions are usage error and file I/O failure; neither is recoverable.)

**State-write (Step 3):** update the run-state file's frontmatter with `draft_path: [DRAFT_PATH]`, `filename: [filename]`, `input_mode: [file | paste]`. Update `last_completed_step: 3` and `last_updated`. Without this, a compaction-induced resume cannot reconstruct the draft path and filename used elsewhere in the run (final-report save, log entries).

### Step 3.5 — Build paragraph map

Run:
```
python3 .claude/scripts/extract_paragraphs.py [DRAFT_PATH] > memory/staging/paragraphs-[run-id].json
```
Read the JSON output and store as [PARAGRAPH_MAP].

[PARAGRAPH_MAP] is injected into every agent prompt in this run (primary agents, canonical agents, challenger, presentation agent). Agents must report locations using these paragraph numbers and must not re-number paragraphs themselves. Without a shared map, two agents reading the same draft can disagree on whether a title or a block quote counts as paragraph 1 — and synthesis steps that match findings by paragraph would silently produce zero matches even when both agents flagged the same passage.

**State-write (Step 3.5):** the JSON output is already on disk at the path above. Append to state file body:
```
### Step 3.5 — Build paragraph map
paragraph_map_path: memory/staging/paragraphs-[run-id].json
```
Update frontmatter `last_completed_step: 3.5` and `last_updated`.

### Step 4 — Load briefs

Brief files are at `.claude/skills/proofread/references/` relative to the graph root (current working directory). Do not guess alternative paths — if any Read fails, report the failure and log STEP:abort.

Read and store three brief variables:

**[SURFACE_BRIEF]:**
Read `.claude/skills/proofread/references/surface.md` in full. Store as [SURFACE_BRIEF].

**[CONSISTENCY_BRIEF]:**
Read `.claude/skills/proofread/references/consistency.md` in full. Store as [CONSISTENCY_BRIEF].

**[REGISTER_BRIEF]:**
If essay type is **research**: Read `.claude/skills/proofread/references/register-research.md` in full.
If essay type is **personal / application / other**: Read `.claude/skills/proofread/references/register-personal.md` in full.
Store as [REGISTER_BRIEF].

All three stored in executor context. Inlined verbatim into respective agent prompts. Never written to files. Do not summarise or abbreviate.

For the canonical field-name contract that brief outputs and synthesis matching must conform to, see `.claude/skills/proofread/references/field-name-standard.md`. Do not rename a field in a brief without updating the standard and synthesis logic together.

**State-write (Step 4):** brief content is held in executor memory only (it is reloaded from disk by re-reading the brief files on resume — no need to persist the content itself). Append a marker to state file body so resume detects briefs were loaded:
```
### Step 4 — Load briefs
briefs_loaded: true
```
Update frontmatter `last_completed_step: 4` and `last_updated`. On resume after Step 4, the executor re-reads the brief files from disk (they are deterministic and version-controlled).

### Step 4.5 — Pre-scans

Two scripts run before primary agents dispatch. Each replaces a search problem (mechanical, exhaustive, deterministic) with the agent's real job (judgment in context).

**British spelling prescan (Check 3):**
```
python3 .claude/skills/proofread/scripts/check_british_spelling.py [DRAFT_PATH] > memory/staging/spelling-[run-id].json
```
Read the output and store as [SPELLING_PRESCAN]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — check_british_spelling.py failed` and exit. The script strips quoted material before scanning (`"..."` regions are excluded), so every instance returned is in the writer's own prose. This eliminates the largest source of false positives in Check 3 — agents flagging American spelling inside directly quoted source material.

**Consistency prescan (Check 4):**
```
python3 .claude/skills/proofread/scripts/check_consistency.py [DRAFT_PATH] > memory/staging/consistency-[run-id].json
```
Read the output and store as [CONSISTENCY_CANDIDATES]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — check_consistency.py failed` and exit. The script finds all word/phrase variant groups across the document mechanically. Consistency agents then focus on the judgment task — assessing which variations are intentional — rather than the search task, which agents do unreliably over long texts.

**State-write (Step 4.5):** the prescan outputs are already on disk at the paths above. Append to state file body:
```
### Step 4.5 — Pre-scans
spelling_prescan_path: memory/staging/spelling-[run-id].json
consistency_candidates_path: memory/staging/consistency-[run-id].json
```
Update frontmatter `last_completed_step: 4.5` and `last_updated`.

### Step 5 — Dispatch primary agents

Compose six agent prompts and dispatch all in parallel.

---

**Surface agents ProofSurface-A-[run-id] and ProofSurface-B-[run-id] — identical prompts:**

```
You are a surface proofreader. Find errors and inconsistencies only — do NOT rewrite passages, do NOT edit source files, do NOT write to any file.

Read [DRAFT_PATH] in full. If lines begin with `- ` (Logseq bullet markers), treat those lines as prose paragraphs — do NOT flag the leading `- ` as a stray character.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

**Verify-by-opening-words rule:** when you write a finding's `Location: paragraph [n]`, take the first 4-6 words of the paragraph that contains your finding from the draft, find a matching `opening_words` value in the PARAGRAPH MAP, and use *that* `paragraph` number. If your quoted opening does not match any `opening_words` in the map, you have miscounted — recount and use the map. Your own count is not authoritative; the map is. Reporting Para 5 for "I earned my B.Sc..." (which the map shows is Para 3) silently misroutes the writer to the wrong place to revise.

BRITISH SPELLING PRESCAN (Check 3): [SPELLING_PRESCAN]
All instances shown above are in the writer's own prose — quoted material has already been excluded by the script. For each: verify in context, confirm or dispute, and report any genuine instances using the brief's Check 3 finding format. Then run Checks 1, 2, and the Unrecognised terms section independently — these have no prescan.

BRIEF:
[SURFACE_BRIEF — paste full content verbatim here]

Run all checks listed in the brief. Return findings using the exact format specified in the brief.
```

---

**Consistency agents ProofConsist-A-[run-id] and ProofConsist-B-[run-id] — identical prompts:**

```
You are a consistency proofreader. Find consistency errors only — do NOT rewrite passages, do NOT edit source files, do NOT write to any file.

Read [DRAFT_PATH] in full. If lines begin with `- ` (Logseq bullet markers), treat those lines as prose paragraphs.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

**Verify-by-opening-words rule:** when you write a finding's `Location: paragraph [n]`, take the first 4-6 words of the paragraph that contains your finding from the draft, find a matching `opening_words` value in the PARAGRAPH MAP, and use *that* `paragraph` number. If your quoted opening does not match any `opening_words` in the map, you have miscounted — recount and use the map. Your own count is not authoritative; the map is. Reporting Para 5 for "I earned my B.Sc..." (which the map shows is Para 3) silently misroutes the writer to the wrong place to revise.

CANDIDATE VARIANT GROUPS (Check 4): [CONSISTENCY_CANDIDATES]
These groups were found by mechanical search across the document. Your task is the judgment, not the search: assess each group and decide whether the variation is intentional or unintentional. A consistent observable pattern signals intent — full form on first mention then abbreviated form afterwards, or one form exclusively inside direct quotations and another in the writer's own prose. Arbitrary alternation with no observable pattern is likely unintentional. Flag only the unintentional variations using the brief's Check 4 finding format. Apply the brief's rules for intentional patterns.

BRIEF:
[CONSISTENCY_BRIEF — paste full content verbatim here]

Run all checks listed in the brief. Return findings using the exact format specified in the brief.
```

---

**Register agents ProofRegister-A-[run-id] and ProofRegister-B-[run-id] — identical prompts:**

```
You are a register quality proofreader. Find register quality errors only — do NOT rewrite passages, do NOT edit source files, do NOT write to any file.

Read [DRAFT_PATH] in full. If lines begin with `- ` (Logseq bullet markers), treat those lines as prose paragraphs.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

**Verify-by-opening-words rule:** when you write a finding's `Location: paragraph [n]`, take the first 4-6 words of the paragraph that contains your finding from the draft, find a matching `opening_words` value in the PARAGRAPH MAP, and use *that* `paragraph` number. If your quoted opening does not match any `opening_words` in the map, you have miscounted — recount and use the map. Your own count is not authoritative; the map is. Reporting Para 5 for "I earned my B.Sc..." (which the map shows is Para 3) silently misroutes the writer to the wrong place to revise.

BRIEF:
[REGISTER_BRIEF — paste full content verbatim here]

Run all checks listed in the brief. Return findings using the exact format specified in the brief.
```

---

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch** — Agents: ProofSurface-A-[run-id], ProofSurface-B-[run-id], ProofConsist-A-[run-id], ProofConsist-B-[run-id], ProofRegister-A-[run-id], ProofRegister-B-[run-id]
```

Description strings must be **exactly**: `ProofSurface-A-[run-id]`, `ProofSurface-B-[run-id]`, `ProofConsist-A-[run-id]`, `ProofConsist-B-[run-id]`, `ProofRegister-A-[run-id]`, `ProofRegister-B-[run-id]` — copy verbatim. The coverage check identifies agents by their description string to decide whether a re-dispatch is needed; if the dispatch log records one name and the coverage check looks for another, the re-dispatch fails silently and the skill cannot recover from agent failures. Exactness here is recovery infrastructure, not style.

Dispatch all six in parallel (subagent_type: `Explore`).

Show: "Six proofreader agents running (surface, consistency, register)…"

### Step 5.4 — Persist each agent's raw response to disk

Subagents dispatched with `subagent_type: Explore` cannot use the `Write` tool — they are read-only by design (this is enforced by the Explore agent profile, not by the skill, and trying to make agents Write produces refusals like "I cannot save the file as instructed because the Write tool is not available"). Therefore the **executor** persists each returned agent's response to disk, not the agent itself.

After each primary agent dispatch in Step 5 returns, the executor writes the agent's full response text to `memory/staging/proofread-[run-id]/{agent-id}.md` using the `Write` tool. The filename matches the agent's description string (e.g. `ProofSurface-A-[run-id].md`). This persistence makes Step 5.5 (location correction) and resume-after-compaction both possible — the executor's working memory of an agent's output is volatile; the on-disk copy isn't.

State-write: append to state file body:
```
### Step 5.4 — Agent outputs persisted
agent_outputs_dir: memory/staging/proofread-[run-id]/
```
Update frontmatter `last_completed_step: 5.4`.

### Step 5.5 — Correct finding locations (deterministic)

Before synthesis, run the location-correction script over each returned agent's raw output:

```
python3 .claude/scripts/correct_finding_locations.py [DRAFT_PATH] memory/staging/proofread-[run-id]/{agent-id}.md --out memory/staging/proofread-[run-id]/{agent-id}-corrected.md 2>> memory/staging/proofread-[run-id]/location-corrections.log
```

For each finding the script extracts the `Current text:` quote, searches the draft for it, and rewrites that finding's `Location: paragraph [n]` to whatever paragraph the script finds the quote in. Mismatches are corrected silently; unmatched quotes (script can't find the quote in the draft) are logged to `location-corrections.log` and the agent's claim is preserved.

**Why this exists:** PARAGRAPH MAP injection plus the verify-by-opening-words rule reduce paragraph-mislabel rate but don't eliminate it — some agents read the rule and apply it, others ignore it. For values where errors silently misroute the writer (a finding labelled Para 5 when it's in Para 3 sends the writer to the wrong place), promptcraft has a ceiling. Deterministic post-processing overwrites agent claims with truth from disk. The script's logic is simple enough — find quote in draft, look up paragraph — and the rule "agent claim loses to disk truth" is unambiguous. This collapses paragraph-numbering to a single source of truth (the draft).

After the script runs for each agent: replace `[agent's raw output]` with `[agent's corrected output]` in the executor's working set. Synthesis (Step 6) operates on corrected outputs.

State-write: append to state file body:
```
### Step 5.5 — Location correction
corrected_outputs_dir: memory/staging/proofread-[run-id]/
corrections_log: memory/staging/proofread-[run-id]/location-corrections.log
```
Update frontmatter `last_completed_step: 5.5`.

### Step 6 — Coverage check + synthesis

**Coverage check:** All six returned? For each missing agent: before re-dispatching, append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch** — Re-dispatch: [agent-id] (first attempt failed)
```
Re-dispatch once, wait. If fails again: append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch** — Failed: [agent-id] (both attempts failed)
```
Record as Agent-failed: [agent-id].

For each returned agent: verify either a `## Finding` section or a `## No findings` / `## Coverage` section is present in the output. If neither is present: treat as partial failure — note "Agent [X] returned no structured findings" in output and continue.

**Pair failure handling:**
- If both agents of a pair failed: that check group is unavailable. [SURFACE_FINDINGS] / [CONSISTENCY_FINDINGS] / [REGISTER_FINDINGS] for that pair = empty. Note in output header: "Note: [Surface / Consistency / Register] agents unavailable — [check numbers] not included."
- If one agent of a pair failed: treat all surviving agent's findings as UNVERIFIED for that group.

**Synthesis — per pair:**

Match findings within each pair. Match criterion: same Check number AND "Current text:" quoted is identical or one is a substring of the other.
- Both agents flag the same passage for the same check → confidence = **HIGH**
- Only one agent flags a passage → confidence = **UNVERIFIED**

For HIGH findings where agents' content differs (Proposed fix for Check 1–3; Pattern/Concern for Check 4–5): use the A-agent's version; append "(description differs between agents)".

Store as:
- [SURFACE_FINDINGS] — surface pair synthesis (Checks 1–3), tagged HIGH or UNVERIFIED. Each finding retains all fields from the brief's ## Finding block (Location, Current text, Proposed fix, Check, Severity). Never drop UNVERIFIED findings.
- [CONSISTENCY_FINDINGS] — consistency pair synthesis (Check 4), tagged HIGH or UNVERIFIED. Each finding retains all fields from the brief's ## Finding block (Location, Current text, Pattern, Concern, Check, Severity). No "Proposed fix" — interpretive judgments; the writer determines the correction.
- [REGISTER_FINDINGS] — register pair synthesis (Check 5), tagged HIGH or UNVERIFIED. Each finding retains all fields from the brief's ## Finding block (Location, Current text, Pattern, Concern, Check, Severity). No "Proposed fix" — interpretive judgments; the writer determines the correction.

UNVERIFIED findings (one agent flagged, the other didn't) are kept, not dropped. They may be real — the writer needs to see them to make that judgment. Dropping them removes that option silently and turns a single agent miss into invisible data loss.

**Collect [UNRECOGNISED_WORDS]:** Take the union of both surface agents' `## Unrecognised terms` lists. Deduplicate. If both agents have "None identified": [UNRECOGNISED_WORDS] = empty. If a surface agent's output lacks the `## Unrecognised terms` section entirely, treat that agent's contribution as "None identified". Format [UNRECOGNISED_WORDS] as one term per line.

**Cross-Surface/Consistency merge check:**

After per-pair synthesis is complete: for each Check 3 finding in [SURFACE_FINDINGS], compute a **normalised match key** — the case-folded, hyphen-stripped form of the flagged word, taken from BOTH the Check 3 `Current text` (the American variant) AND the Check 3 `Proposed fix` (the British variant). Then check each Check 4 finding in [CONSISTENCY_FINDINGS]: extract its `Current text`, apply the same normalisation (case-fold + hyphen-strip), and test whether the normalised form matches **either** of the Check 3 normalised keys (American OR British form). The merge key must be normalised because Check 4 agents may flag any variant from the consistency prescan as their `Current text` (the American form, the British form, or another spelling) — exact-string matching against only one form fails silently when the agent picks the other.

If match found: merge into one compound finding. Surface concern (Check 3: Proposed fix) + Consistency concern (Check 4: Pattern + Concern). Use the higher severity (Check 3 = High → merged = High). Replace the two separate entries with the merged entry in [SURFACE_FINDINGS]; remove the matched Check 4 entry from [CONSISTENCY_FINDINGS]. Add to the merged finding: `⚠ Also flagged by Consistency check: [Pattern description from the Check 4 finding]`.

If no match: keep entries separate.

The presentation agent (Step 11) labels merged findings "⚠ Compound: spelling + consistency."

**Coverage failure notes:** record any "[Surface / Consistency / Register] agents unavailable — [check numbers] not included" notes produced by this step's coverage check into a single text file at `memory/staging/proofread-[run-id]/coverage-notes.md` (one note per line; empty file if no pairs failed). Step 11 reads this file when filling the STATUS NOTES placeholder for the presentation agent. Without on-disk persistence, a compaction-induced resume to Step 11 has no record of which agent pairs failed.

**State-write (Step 6):** write [SURFACE_FINDINGS], [CONSISTENCY_FINDINGS], [REGISTER_FINDINGS], [UNRECOGNISED_WORDS], and the coverage notes file to disk so a compaction-induced resume can reload them. Append to state file body:
```
### Step 6 — Synthesis
synthesised_findings_path: memory/staging/proofread-[run-id]/synthesised-findings.md
unrecognised_words_path: memory/staging/proofread-[run-id]/unrecognised-words.txt
coverage_notes_path: memory/staging/proofread-[run-id]/coverage-notes.md
```
Update frontmatter `last_completed_step: 6`.

### Step 7 — Canonical check

If [CANONICAL_STATUS] = "unavailable" OR [UNRECOGNISED_WORDS] is empty: [MIGRATION_FINDINGS] = empty. [STILL_UNKNOWN] = empty. Skip to Step 8.

**Canonical-1 pair — project vocabulary check (two identical agents):**

Compose prompt (ProofCanon1-A-[run-id] and ProofCanon1-B-[run-id] receive the same prompt):
```
You are the canonical vocabulary checker for a proofreading run.

Read [PROJECT_PATH] in full. Find the section `## Proofread Context`. Within it, find `canonical_terms`. Load the list. If the file does not exist, if the section is missing, or if canonical_terms is empty: treat the canonical list as empty and report all terms as Unresolved.

PARAGRAPH MAP: [PARAGRAPH_MAP]
(Reference only — this check does not report paragraph locations, but the map is provided for consistency across agents in this run.)

UNRECOGNISED TERMS FROM DRAFT:
[UNRECOGNISED_WORDS — one term per line]

For each term: check against the canonical_terms list.

Return:
## Matched — correct
[Terms in canonical list and spelled correctly in the draft. One per line: "term — matches canonical form". If none: "None."]

## Matched — incorrect
[Terms in canonical list but spelled differently in the draft. One per line: "draft form → canonical form". If none: "None."]

## Near-matched
[Terms not in canonical list but close enough to a listed term to be a likely variant (one or two character difference, or common transliteration variant). One per line: "draft form — possible variant of: [canonical term]". If none: "None."]

## Unresolved
[Terms not found in canonical list and no near-match. One per line. If none: "None."]
```

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Agents: ProofCanon1-A-[run-id], ProofCanon1-B-[run-id]
```

Description strings must be **exactly**: `ProofCanon1-A-[run-id]`, `ProofCanon1-B-[run-id]` — copy verbatim.

Dispatch both in parallel (subagent_type: `Explore`).

**Coverage check (Canonical-1 pair):** Both returned? For each missing: before re-dispatching, append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Re-dispatch: [agent-id] (first attempt failed)
```
Re-dispatch once. If fails again: append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Failed: [agent-id] (both attempts failed)
```
Record as Agent-failed: [agent-id].

If both failed: [MIGRATION_FINDINGS] = empty. [STILL_UNKNOWN] = [UNRECOGNISED_WORDS]. Note "canonical check unavailable" in output header. Skip to Step 8.
If one failed: treat all surviving agent's findings as UNVERIFIED for this step. Proceed with synthesis.

**Synthesis (Canonical-1):**

For each term in [UNRECOGNISED_WORDS], compare both agents' classifications and apply this table. Where agents disagree, the rule is conservative: a discrepancy from one agent surfaces as UNVERIFIED rather than being silently dropped.

**Canonical-finding format (when an outcome row writes "→ [SURFACE_FINDINGS]"):** synthesise a finding entry in the same field structure as Surface Check 3 findings (per `references/field-name-standard.md`), so the challenger and presentation agents process canonical corrections identically to spelling corrections:

```
## Finding [n]
Location: paragraph [p], sentence [m] of the paragraph, [opening words of the sentence] — taken from the first occurrence of the term in [DRAFT_PATH] (use the [PARAGRAPH_MAP] to look up paragraph; the term may appear in multiple paragraphs but list the first)
Current text: "[unrecognised term as it appears in the draft]"
Proposed fix: "[canonical correction agreed by agents, or A-agent's correction if disagreement]"
Check: 3
Severity: High (matched-incorrect / near-matched canonical) | Medium (canonical-correct but informational only — discarded, not entered)
```

The Check value is `3` because canonical corrections are spelling/terminology corrections — Check 3 is "British spelling and project canonical terms" by extension. The presentation agent surfaces them in the Check 3 section per `references/presentation-format.md`.

| Agent A classification | Agent B classification | Outcome |
|---|---|---|
| Matched-incorrect (same correction) | Matched-incorrect (same correction) | **HIGH** correction → [SURFACE_FINDINGS] |
| Matched-incorrect (different corrections) | Matched-incorrect (different corrections) | **UNVERIFIED**; use A-agent's correction |
| Near-matched (same canonical form) | Near-matched (same canonical form) | **HIGH** correction → [SURFACE_FINDINGS] |
| Near-matched (different canonical forms) | Near-matched (different canonical forms) | **UNVERIFIED**; use A-agent's canonical form |
| Matched-incorrect | Near-matched | **UNVERIFIED**; use the Matched-incorrect correction (more precise classification) |
| Matched-incorrect or Near-matched | Unresolved | **UNVERIFIED**; use the matching agent's correction |
| Unresolved | Unresolved | add term to [UNRESOLVED] |
| Matched-correct | Matched-correct | discard (no finding) |
| Matched-correct | Matched-incorrect or Near-matched | **UNVERIFIED** correction → [SURFACE_FINDINGS] |
| Matched-correct | Unresolved | add term to [UNRESOLVED] (UNVERIFIED) |

Order is symmetric (swap A and B columns and the outcome is the same).

[UNRESOLVED] = terms routed to that bucket above.

**Canonical-2 pair — cross-project and global check (two identical agents):**

Only dispatch if [UNRESOLVED] is not empty. If [UNRESOLVED] is empty: [MIGRATION_FINDINGS] = empty. [STILL_UNKNOWN] = empty. Show: "Canonical vocabulary check complete." Proceed to Step 8.

Compose prompt (ProofCanon2-A-[run-id] and ProofCanon2-B-[run-id] receive the same prompt):
```
You are the cross-project canonical vocabulary checker for a proofreading run.

CURRENT PROJECT: [PROJECT_NAME]

PARAGRAPH MAP: [PARAGRAPH_MAP]
(Reference only — this check does not report paragraph locations.)

UNRESOLVED TERMS (not found in current project's canonical list):
[UNRESOLVED — one term per line]

Step 1: Glob `memory/projects/project-*.md` to find all project files. For each file: read it in full. Find `## Proofread Context → canonical_terms`. Note the project name (from the filename: project-[name].md) and its terms list. If the section or `canonical_terms` field is absent in a file, that file contributes no terms.

Step 2: Read `memory/projects/project-general.md` in full. Find `## Global Canonical Terms`. Load that list separately. (If project-general.md is the current project, still read it — the Global Canonical Terms section is distinct from the project's own canonical_terms. If `project-general.md` does not exist or the section is missing, treat the global list as empty.)

Step 3: For each unresolved term, check against all project canonical_terms lists and the Global Canonical Terms list. A match requires the same spelling or a near-variant (one or two character difference).

**Search scope — strict:** Read ONLY files matching `memory/projects/project-*.md`. Do NOT read `memory/memory-glossary.md`, `memory/people/`, page files in `pages/`, the draft, or any other location. A "match" requires the term to appear inside a `## Proofread Context → canonical_terms` field, NOT inside prose, biographies, supervisor notes, or any other section. A mention of a person, term, or title elsewhere in a project file (or anywhere else in the graph) is NOT a canonical match — those mentions go in "Still unknown" if no canonical_terms entry exists. The point of canonical_terms is that it is an explicit, opted-in vocabulary list; only entries Vaidehi has deliberately recorded there count as matches.

Return:

## Found in global terms
[Terms found in ## Global Canonical Terms in project-general.md. One per line: "term — suggest: add to [CURRENT PROJECT] canonical list". If none: "None."]

## Found in other project(s)
[Terms found in another project's canonical_terms (not the current project). One per line: "term — found in: [project name(s)] — suggest: add to [CURRENT PROJECT] canonical list[; promote to Global Canonical Terms if found in 2+ projects]". If none: "None."]

## Still unknown
[Terms not found anywhere across all project files or global terms. One per line. If none: "None."]
```

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Agents: ProofCanon2-A-[run-id], ProofCanon2-B-[run-id]
```

Description strings must be **exactly**: `ProofCanon2-A-[run-id]`, `ProofCanon2-B-[run-id]` — copy verbatim.

Dispatch both in parallel (subagent_type: `Explore`).

**Coverage check (Canonical-2 pair):** Both returned? For each missing: before re-dispatching, append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Re-dispatch: [agent-id] (first attempt failed)
```
Re-dispatch once. If fails again: append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-canonical** — Failed: [agent-id] (both attempts failed)
```
Record as Agent-failed: [agent-id].

If both failed: [STILL_UNKNOWN] = [UNRESOLVED]; [MIGRATION_FINDINGS] = empty. Show: "Canonical vocabulary check complete." Proceed to Step 8.
If one failed: treat all surviving agent's findings as UNVERIFIED for this step. Proceed with synthesis.

**Synthesis (Canonical-2):**

For each term in [UNRESOLVED]: compare both agents' outputs.
- Both agents place the term in "Found in global terms" or "Found in other project(s)" with the same match → confidence = **HIGH**
- One agent finds the term; the other places it in "Still unknown" → confidence = **UNVERIFIED**; use the finding agent's result
- One agent places the term in "Found in global terms" and the other in "Found in other project(s)": include both results in [MIGRATION_FINDINGS] tagged UNVERIFIED. Present both migration recommendations; the writer determines which applies.
- Both agents place the term in "Still unknown" → add to [STILL_UNKNOWN]

Collect [MIGRATION_FINDINGS] = all HIGH and UNVERIFIED findings from the "Found in global terms" and "Found in other project(s)" sections (tagged with confidence). [STILL_UNKNOWN] = terms where both agents returned "Still unknown".

**State-write (Step 7):** write [UNRESOLVED], [MIGRATION_FINDINGS], and [STILL_UNKNOWN] to disk. Append to state file body:
```
### Step 7 — Canonical check
canonical_results_path: memory/staging/proofread-[run-id]/canonical-results.md
unresolved_path: memory/staging/proofread-[run-id]/unresolved.txt
migration_findings_path: memory/staging/proofread-[run-id]/migration-findings.md
still_unknown_path: memory/staging/proofread-[run-id]/still-unknown.txt
```
Update frontmatter `last_completed_step: 7`.

Show: "Canonical vocabulary check complete."

### Step 8 — Canonical resolution + write-back

If [STILL_UNKNOWN] is empty: [NEW_CANONICAL_TERMS] = empty. Skip to Write-back.

**Writer confirmation (if [STILL_UNKNOWN] not empty):**

Use AskUserQuestion: "These terms weren't found in any project vocabulary. For each, type the correct spelling — or leave blank to skip." Present the [STILL_UNKNOWN] list. User types corrections via Other field.

Parse the Other field: extract confirmed term → canonical spelling pairs. Store as [NEW_CANONICAL_TERMS]. Terms left blank or not addressed: skip.

**Write-back:**

If [NEW_CANONICAL_TERMS] not empty:
- Read [PROJECT_PATH]. Find `## Proofread Context`. Append new terms under `canonical_terms`. If the section does not exist: create it.
- If [PROJECT_PATH] = `memory/projects/project-general.md` and the file does not exist: create it with:
  ```
  title:: General
  type:: project
  status:: in-progress

  ## Proofread Context
  canonical_terms:
  - [new terms]

  ## Global Canonical Terms
  ```

If [MIGRATION_FINDINGS] includes any "promote to Global Canonical Terms" recommendations: read `memory/projects/project-general.md`, append the promoted terms under `## Global Canonical Terms`. Create the section if absent.

**State-write (Step 8):** persist [NEW_CANONICAL_TERMS] and [MIGRATION_FINDINGS] as files (not literal lists in the state file) so a compaction-induced resume can determine whether write-back already happened and what was written. Write [NEW_CANONICAL_TERMS] to `memory/staging/proofread-[run-id]/new-canonical-terms.txt` (one term per line; empty file if none). Write [MIGRATION_FINDINGS] to `memory/staging/proofread-[run-id]/migration-findings.md` (full finding entries; empty file if none). Append to state file body:
```
### Step 8 — Canonical resolution + write-back
new_canonical_terms_path: memory/staging/proofread-[run-id]/new-canonical-terms.txt
migration_findings_path: memory/staging/proofread-[run-id]/migration-findings.md
write_back_target: [path written, or "(none)"]
global_promotions_path: memory/staging/proofread-[run-id]/global-promotions.txt
```
Update frontmatter `last_completed_step: 8`.

### Step 9 — Dispatch challenger

Combine all synthesised findings into unified [ALL_FINDINGS]: [SURFACE_FINDINGS] then [CONSISTENCY_FINDINGS] then [REGISTER_FINDINGS], renumbered sequentially (Finding 1, Finding 2, …). Canonical corrections from Step 7 are already incorporated in [SURFACE_FINDINGS].

**Empty-findings guard:** if [ALL_FINDINGS] is empty (every primary pair returned zero findings, or every primary pair both-failed), do NOT dispatch the challenger pair. Set [CHALLENGER_VERDICTS] = empty. Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-challenger** — Skipped: [ALL_FINDINGS] empty, no findings to adjudicate.
```
Skip to Step 10's State-write (which records [CHALLENGER_VERDICTS] = empty), then Step 11. The presentation agent receives empty inputs and produces a clean "no findings" report per `references/presentation-format.md`.

Compose challenger prompt (identical for both agents):

```
You are the challenger agent for a proofreading check.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers in your verdict reasoning when referring to passages.

ALL FINDINGS FROM PRIMARY AGENTS:
[ALL_FINDINGS — each finding tagged HIGH or UNVERIFIED, sequentially numbered, reproduced in full]

For each finding: assess whether it is a genuine error or genuine concern given the essay type, the writer's evident conventions, and the passage in context.

Rules:
- Check 3 (British spelling): do NOT uphold a finding if the flagged text is inside directly quoted source material.
- Check 4 (Consistency): do NOT uphold a finding if the variation follows a consistent, observable pattern that signals intentionality — for example, the full form used on first mention then an abbreviated or shortened form used throughout, or a term appears in one form exclusively inside direct quotations and in another form in the writer's own prose. A variation that switches arbitrarily with no consistent pattern is likely unintentional. If you cannot determine intent from the observable text: return AMBIGUOUS with a specific question (e.g., "Is 'scarf' used intentionally in paragraph 3 to distinguish it from 'dupatta', or is this an unintentional slip?").
- Check 5 (Register quality): do NOT uphold a finding if the register shift is present consistently throughout (consistent informal = not a shift).
- Compound findings (findings whose text includes the note "⚠ Also flagged by Consistency check:" — these carry both a Check 3 British spelling concern and a Check 4 consistency concern): assess each concern by its applicable rule. Return UPHELD if either concern is upheld; DISPUTED only if both concerns are independently disputed; AMBIGUOUS if any concern is ambiguous.
- For all checks: state your reasoning first, then your verdict. State the verdict label exactly once, at the end of your reasoning. Do not pre-commit a label at the top of your reasoning. Reasoning-then-verdict matters because a label committed up front constrains the reasoning that follows; when the label comes last, the reasoning leads to the conclusion, which produces better verdicts on ambiguous findings.
- For Check 1–3 findings: UPHELD means the correction is appropriate.
- For Check 4–5 findings: UPHELD means the concern is genuine and worth the writer's attention. (No proposed fix to endorse — these findings present a pattern and concern for the writer to act on.)

Return one verdict per finding:
[UPHELD] — confirmed error or genuine concern
[DISPUTED: reason] — not an error or concern in context; explain specifically
[AMBIGUOUS: question] — cannot decide; present the specific question for the writer

## Challenger assessment: Finding [n]
Agent confidence: [HIGH / UNVERIFIED] | Check: [1–5]
Current text: "[exact quote as reported by primary agents]"
[Reasoning — explain why this is or isn't an error/concern given context]
Verdict: [UPHELD / DISPUTED: reason / AMBIGUOUS: question]
```

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-challenger** — Agents: ProofChallenger-A-[run-id], ProofChallenger-B-[run-id]
```

Description strings must be **exactly**: `ProofChallenger-A-[run-id]`, `ProofChallenger-B-[run-id]` — copy verbatim.

Dispatch both in parallel (subagent_type: `Explore`).

**State-write (Step 9):** write [ALL_FINDINGS] to disk before challenger dispatch returns, so a compaction-induced resume of Step 10 can load it. Append to state file body:
```
### Step 9 — Combined findings + challenger dispatch
all_findings_path: memory/staging/proofread-[run-id]/all-findings.md
challengers_dispatched: [ProofChallenger-A-[run-id], ProofChallenger-B-[run-id]]
```
Update frontmatter `last_completed_step: 9`.

Show: "Challengers running…"

### Step 10 — Challenger coverage check + synthesis

**Coverage check:** Both challengers returned? For each missing: before re-dispatching, append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-challenger** — Re-dispatch: [agent-id] (first attempt failed)
```
Re-dispatch once, wait. If fails again: append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-challenger** — Failed: [agent-id] (both attempts failed)
```

**Challenger synthesis:**

Apply the synthesis rules in `.claude/skills/proofread/references/challenger-synthesis-rules.md`. The rules cover: match criterion (same finding number), the nine verdict-confidence labels (confirmed, confirmed-disputed, split, ambiguous, partial-upheld, partial-disputed, partial-ambiguous, partial-unaddressed, unverified-challenger), one-challenger-failed and both-challengers-failed handling, and the storage format for [CHALLENGER_VERDICTS].

Read the rules file in full before synthesising. Store results as [CHALLENGER_VERDICTS], keyed by finding number, in the format the rules file specifies.

**State-write (Step 10):** write [CHALLENGER_VERDICTS] to disk so a compaction-induced resume of Step 11 can reload it. Append to state file body:
```
### Step 10 — Challenger coverage check + synthesis
challenger_verdicts_path: memory/staging/proofread-[run-id]/challenger-verdicts.md
```
Update frontmatter `last_completed_step: 10` and `last_updated`.

### Step 11 — Dispatch presentation agent

Dispatch ProofPresentation-[run-id] (single agent).

Before constructing the prompt: substitute the `[Coverage failure notes recorded in Step 6 — e.g., "Note: Surface agents unavailable — Checks 1–3 not included." Pass an empty string if no pairs failed.]` placeholder (it appears below in STATUS NOTES) with any coverage failure notes recorded in Step 6. If no pairs failed, pass an empty string.

Agent prompt:
```
You are the presentation agent for a proofreading run. Your task is to organise all synthesised findings for the writer. Do NOT rewrite, edit, or re-evaluate findings — present what was determined by the primary agents and challenger.

Read `.claude/skills/proofread/references/presentation-format.md` in full — it defines the output sections, the per-section selection rules, and the coverage-table bucket mapping.

Read `.claude/skills/proofread/assets/report-header-template.md` — use it as the report header, filling in the bracketed fields and including only the status notes that apply to this run.

Read [DRAFT_PATH] in full to confirm paragraph boundaries for the by-location view (the PARAGRAPH MAP gives opening-words snippets, but reading the draft lets you confirm each paragraph in context).

ESSAY TYPE: [type] | PROJECT: [PROJECT_NAME]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers — every finding's `Location:` field already references this map.

SYNTHESISED FINDINGS:
[ALL_FINDINGS — each finding tagged HIGH or UNVERIFIED, sequentially numbered, reproduced in full]

CHALLENGER VERDICTS:
[CHALLENGER_VERDICTS — one line per finding number, verdict confidence label per `references/challenger-synthesis-rules.md`]

STATUS NOTES (for the header — pass through verbatim):
[Coverage failure notes recorded in Step 6 — e.g., "Note: Surface agents unavailable — Checks 1–3 not included." Pass an empty string if no pairs failed.]

MIGRATION FINDINGS:
[MIGRATION_FINDINGS — from canonical check, or "none"]

Produce the report exactly as `references/presentation-format.md` specifies. Present all findings inline. Do not truncate, do not summarise behind a save step, do not omit findings to keep the output short — truncation is silent data loss; the writer cannot tell what was omitted. Omit only sections that have no qualifying findings (the format file lists which).

**Output the full report as the direct content of your response.** Do NOT summarise what you produced ("Report complete. Quick wins: …"); do NOT describe your actions; do NOT say "the session log has been updated" in lieu of the report. The executor relays your response verbatim to the writer — if you summarise, the writer never sees the findings. Every finding entry, every section heading, every line of the coverage table must appear in your response output.

After producing the report, append to `memory/staging/session-log-[YYYY-MM-DD].md` the STEP:complete line specified at the bottom of `references/presentation-format.md`.
```

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-presentation** — Agent: ProofPresentation-[run-id]
```

Description string must be **exactly**: `ProofPresentation-[run-id]` — copy verbatim.

Dispatch (subagent_type: `Explore`).

Show: "Presentation agent running…"

**Coverage check:** Agent returned? If missing: before re-dispatching, append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-presentation** — Re-dispatch: ProofPresentation-[run-id] (first attempt failed)
```
Re-dispatch once, wait. If fails again: append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:dispatch-presentation** — Failed: ProofPresentation-[run-id] (both attempts failed)
```
If presentation agent failed twice: executor renders output directly from [ALL_FINDINGS] and [CHALLENGER_VERDICTS] using the output format above, then appends STEP:complete to session log.

**On successful completion (or executor-fallback completion):** save the final report text to `memory/staging/proofread-[run-id]/final-report.md`, update the state file's frontmatter `status: complete` and `last_completed_step: 11`, and append the Step 11 section to the state file's body with `final_report_path:`. The complete state file is kept on disk; future Step 0 resume checks see `status: complete` and ignore it.

### Step 12 — Save on request

If the user says "save that" or "save the report": write full findings to `memory/staging/proofread-[filename]-[run-id].md`, where `[filename]` is the base filename without extension of the file provided in Step 3, or `paste` if input mode is "paste". Include all sections: quick wins, by location, by type, needs your decision, disputed, migration recommendations, coverage table.

Append to session log:
```
**[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:saved** — Full report written to memory/staging/proofread-[filename]-[run-id].md.
```

---

## Catch-all abort rule

At ANY step, if this skill exits before logging STEP:complete for any reason, the final actions before exit are ALWAYS:

1. Append to `memory/staging/session-log-[YYYY-MM-DD].md`:
   ```
   **[HH:MM:SS] SKILL:proofread RUN:[run-id] STEP:abort** — [reason]
   ```
2. Update the state file at `memory/staging/proofread-state-[run-id].md` frontmatter: `status: abandoned`, `last_updated: [now]`. The state file is kept on disk so a later resume check shows it as abandoned (not in-progress) and ignores it.

Compaction-induced exits are different: if compaction cuts the session before the skill writes STEP:complete, the state file remains `status: in-progress` (because no abort handler ran). On the next /proofread invocation, Step 0 sees the in-progress state and offers the writer Resume / Start fresh. This is the design — abandoned and in-progress are intentionally distinct so the writer can recover compaction-interrupted runs without manual cleanup.
