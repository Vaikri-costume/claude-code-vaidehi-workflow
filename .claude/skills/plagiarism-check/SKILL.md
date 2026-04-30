---
name: plagiarism-check
description: Use this skill whenever Vaidehi wants to check a draft essay for plagiarism risk before submission — whether from inadvertent close paraphrasing, structural mirroring of sources, or voice drift toward source material. Trigger on "check for plagiarism", "is this too close to sources", "plagiarism risk", "check originality", "too similar to source", or before submitting any research essay that engages heavily with primary or secondary sources. Three modes: citation-check (cited sources only), full-scan (all project sources), or voice-only (no source comparison). Particularly important for research essays where foundational sources are engaged closely.
argument-hint: "[optional: draft file path]"
---

# plagiarism-check

Three-mode plagiarism risk check: citation-check (sources cited in the draft), full-scan (all annotated project sources), or voice-only (no source comparison). Tier 1 self-discovery + paired Tier 2 per-source agents + dual structural and voice pairs + dual challenger + presentation agent.

---

## Invocation

```
/plagiarism-check [optional: file path]
```

---

## Execution

**Mid-cycle output rule:** Show brief dispatch signals after Steps 5, 6, 7, 9, and 11. Allow AskUserQuestion in Steps 0, 2, 5, 6 (post-Tier-1 scope gate), and 6 (voice reference confirmation). Do not narrate synthesis or intermediate analysis.

**Compaction survival is mandatory.** Every step persists outputs to disk and updates a state file at `memory/staging/plagiarism-check-state-[run-id].md`. Step 0 detects in-progress state files on next invocation and offers Resume / Start fresh. Plagiarism-check is the heaviest of the four skills — Tier 1 (2 agents self-discovering 15+ sources) + Tier 2 (paired per-source dispatches) + structural+voice pairs + dual challenger + presentation. Losing 20+ agent dispatches to a context-window boundary is unacceptable.

### Step 0 — Resume check

Use the Glob tool to find files matching `memory/staging/plagiarism-check-state-*.md`. For each match, read its YAML frontmatter and check `status:`.

- **None found, or all `status: complete` / `status: abandoned`:** continue to Step 1 with a new run_id.
- **Exactly one with `status: in-progress`:** AskUserQuestion: "Found an in-progress plagiarism-check run [run-id] for [draft_path] (last completed step: [last_completed_step], updated [last_updated]). Resume or start fresh?" Options: ["Resume" / "Start fresh"].
  - **Resume:** (1) load every frontmatter field into executor context; (2) for each section under `## Step outputs` up to and including `last_completed_step`, read the referenced files into the corresponding executor variables ([PARAGRAPH_MAP], [SOURCE_LIST], [TIER1_RESULTS], [TIER2_FINDINGS], [SYNTHESISED_STRUCTURAL], [SYNTHESISED_VOICE], [ALL_FINDINGS], [CHALLENGER_VERDICTS], coverage notes, raw agent outputs, corrected agent outputs, raw challenger outputs — whichever exist for the resume point); (3) **if `last_completed_step >= 4`, deterministically re-execute Step 4's brief-loading logic** (read `references/per-source.md` + the appendix matching essay_type → [PER_SOURCE_BRIEF]; read `references/structural.md` → [STRUCTURAL_BRIEF]; read `references/voice.md` → [VOICE_BRIEF]; read `references/tier1.md` → [TIER1_BRIEF] — briefs are deterministic functions of essay_type and version-controlled, not persisted to disk, so the resume protocol must reload them before skipping ahead). Append to session log: `**[HH:MM:SS] SKILL:plagiarism-check RUN:[run-id] STEP:resume** — Resumed from step [last_completed_step]`. Skip Steps 1 through `last_completed_step` and continue from step (last_completed_step + 1).
  - **Start fresh:** rename the state file to `plagiarism-check-state-[old_run_id]-abandoned-[YYYYMMDD-HHMMSS].md` and update its frontmatter `status: abandoned`. Continue to Step 1 with a new run_id.
- **Multiple `status: in-progress`:** AskUserQuestion to list each, let the writer pick one to resume or "Abandon all and start fresh."

**Variable lifecycle (resume protocol — applies to all consumer steps below).** Variables produced by step N are persisted to disk via that step's State-write block. On resume, the Step 0 Resume action above is the single point that loads every persisted variable from disk into executor context — including (a) every frontmatter field (`project_name`, `essay_type`, `mode`, `draft_path`, `filename`, `input_mode`, `voice_reference_path`), (b) every `## Step outputs` file path up to `last_completed_step`, and (c) brief content (re-read from `references/*.md` per the routing rule in Step 4). After Step 0 returns, every variable a consumer step references is in executor context. Consumer steps do NOT need per-step "Load X from disk" instructions.

### Step 1 — Log start

Append to `memory/staging/session-log-[YYYY-MM-DD].md`:
```
**[HH:MM:SS] SKILL:plagiarism-check RUN:[run-id] STEP:start** — Run begun.
```

The run ID is the current timestamp at second precision. **Create the run-state file at `memory/staging/plagiarism-check-state-[run-id].md`** with this initial content:
```
---
run_id: [run-id]
skill: plagiarism-check
draft_path: (set in Step 3)
project_name: (set in Step 2)
essay_type: (set in Step 2)
mode: (set in Step 2)
voice_reference_path: (set in Step 6 if voice mode requires it)
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

**State-write rule (every subsequent step):** at the end of each step, write any new variables to disk under `memory/staging/plagiarism-check-[run-id]/` and append the step's section to the state file body, then update frontmatter `last_completed_step` and `last_updated`.

### Step 2 — Load context

Check for existing context: (1) `memory/projects/project-[name].md → ## Plagiarism Check Context` if a project name was provided at invocation, or (2) `memory/staging/plagiarism-check-context.md` if no project name.

**Path A — context found:** Load it. AskUserQuestion: "I'll use this context — [essay type, mode, project]. Confirm or correct." Options: ["Confirmed — proceed" / "I'll correct via Other"]. Cancel → log `STEP:abort — user cancelled at context confirmation` and exit. If user corrects: update + save to `memory/staging/plagiarism-check-context.md`.

**Path B — no context found:**
1. AskUserQuestion: "Essay type?" Options: ["research" / "personal" / "application" / "other"]. Cancel → abort.
2. AskUserQuestion: "Mode?" Options: ["citation-check (only sources cited in the draft)" / "full-scan (all annotated project sources)" / "voice-only (no source comparison; pure voice/genre drift)"]. Cancel → abort.
3. If mode ≠ "voice-only": AskUserQuestion: "Project name? (enables source discovery)" Options: ["Use General project" / "I'll type it in Other"]. Empty → "general".
4. Save to `memory/staging/plagiarism-check-context.md`.

**State-write (Step 2):** update frontmatter with `project_name`, `essay_type`, `mode`. Update `last_completed_step: 2`.

### Step 3 — Identify draft path

If a file path was provided at invocation: store as [DRAFT_PATH]. Verify it exists. Not found → log abort + exit. Record [filename] (base name without extension), input_mode = "file".

If pasted text: save to `memory/staging/draft-[run-id].md`. Then run `python3 .claude/scripts/strip_markers.py memory/staging/draft-[run-id].md`. If the script exits non-zero: log `STEP:abort — strip_markers.py failed (exit [N])` and exit. Set [DRAFT_PATH], input_mode = "paste", [filename] = "paste".

If neither: AskUserQuestion: "Paste the draft text, or provide a file path." Cancel → abort.

**State-write (Step 3):** update frontmatter with `draft_path`, `input_mode`, `filename`. Update `last_completed_step: 3`.

### Step 3.5 — Build paragraph map

Run:
```
python3 .claude/scripts/extract_paragraphs.py [DRAFT_PATH] > memory/staging/paragraphs-[run-id].json
```
Read and store as [PARAGRAPH_MAP]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — extract_paragraphs.py failed` and exit. Inject into every agent prompt.

**State-write (Step 3.5):** append to state file body:
```
### Step 3.5 — Build paragraph map
paragraph_map_path: memory/staging/paragraphs-[run-id].json
```
Update `last_completed_step: 3.5`.

### Step 4 — Brief composition

Brief / reference files are at `.claude/skills/plagiarism-check/references/`. If any Read fails, log abort.

**[PER_SOURCE_BRIEF]:** Read `references/per-source.md` in full. If essay type is **research**: also read `references/per-source-research.md` and concatenate. If **personal / application / other**: same with `references/per-source-personal.md`.

**[STRUCTURAL_BRIEF]:** Read `references/structural.md` in full.

**[VOICE_BRIEF]:** Read `references/voice.md` in full.

**[TIER1_BRIEF]:** Read `references/tier1.md` in full.

For the field-name contract, see `references/field-name-standard.md`.

**State-write (Step 4):** brief content is held in executor memory only — on resume, the executor re-reads. Append marker:
```
### Step 4 — Brief composition
briefs_loaded: true
```
Update `last_completed_step: 4`.

### Step 5 — Source discovery (citation-check and full-scan only; voice-only skips)

**Voice-only mode:** set [SOURCE_LIST] = empty, [TIER1_RESULTS] = empty. Skip to Step 6 (voice-reference handling).

**Citation-check mode:** Grep [DRAFT_PATH] for `[[…]]` Logseq page links. For each linked page, check whether `pages/[link].md` exists and has `type:: source`. Filter to existing source pages → [SOURCE_LIST]. If empty: AskUserQuestion: "No Logseq page links found in this draft — switch mode?" Options: ["Switch to full-scan" / "Switch to voice-only" / "Cancel"]. Update mode and re-run Step 5 / skip per choice. For citation-check mode, set [TIER1_RESULTS] = all discovered sources labelled `FLAGGED-CITATION` (citation-check assumes the writer's explicit citation already establishes engagement; Tier 2 reviews each cited source for risk per the per-source brief; no scope gate). The `FLAGGED-CITATION` label is distinct from the full-scan-mode labels (`FLAGGED-HIGH`, `FLAGGED-UNVERIFIED`) because citation-check did not run Tier 1 inter-agent agreement; every cited source proceeds to Tier 2 unconditionally.

**Full-scan mode:** dispatch dual Tier 1 agents (`PlagTier1-A-[run-id]` and `PlagTier1-B-[run-id]`, identical prompts, both self-discover via Glob).

Each agent prompt:
```
Read [DRAFT_PATH] in full.
PROJECT: [PROJECT_NAME]
ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations.

BRIEF:
[TIER1_BRIEF — paste full content verbatim]

Use Glob pattern: pages/**/*.md
Filter to files with: type:: source [and project:: [[PROJECT_NAME]] if PROJECT_NAME ≠ "general"]
For each matching source page: Read it. Skip pages with no annotation content (no quoted passages in "..." format).
For each annotated source page, compare against the draft per the brief.

Return per source (per the brief's exact format):
## Source: [slug]
File: [full file path]
FLAGGED — found: "[exact matched phrase]"

OR

## Source: [slug]
File: [full file path]
CLEARED
```

Append to session log: `STEP:dispatch — Agents: PlagTier1-A-[run-id], PlagTier1-B-[run-id]`. Dispatch both in parallel (subagent_type: `Explore`).

**Tier 1 cache (full-scan mode only):** before dispatching, check for `memory/staging/plagiarism-tier1-cache-[PROJECT_NAME].md`. For each source listed there, check current file mtime vs cached mtime. Sources with unchanged mtime: load cached FLAGGED/CLEARED result, exclude from Tier 1 dispatch. If all sources cached and unchanged: skip Tier 1 entirely; load [TIER1_RESULTS] from cache. Append to session log: `STEP:tier1-cache — Loaded [n] cached results. Dispatching Tier 1 for [n] new/changed sources.` After Tier 1 synthesis, write fresh results back to the cache file.

**Coverage check (full-scan only):** Both Tier 1 agents returned? For each missing: re-dispatch once with logged STEP:dispatch line. If both fail: treat all discovered sources as HIGH (fail-safe), append double-fail log.

**Tier 1 synthesis:** both agents return FLAGGED for a source → confidence **HIGH** flagged; one FLAGGED, one CLEARED → confidence **UNVERIFIED** flagged (one agent missed it; safer to investigate); both CLEARED → CLEARED. Store as [TIER1_RESULTS] with each source labelled `FLAGGED-HIGH`, `FLAGGED-UNVERIFIED`, or `CLEARED`. (Tier 1 brief intentionally limits agents to verbatim-match detection only — no risk-level grading. The HIGH/UNVERIFIED labels here come from inter-agent agreement, not from agent self-assessment.)

**Post-Tier-1 scope gate (full-scan mode only):** AskUserQuestion: "Tier 1 complete. [n] sources flagged HIGH (both agents agreed), [n] flagged UNVERIFIED (one agent flagged, one cleared). Proceed with: (a) HIGH only — fastest; (b) HIGH + UNVERIFIED — recommended; (c) cancel." Options: ["HIGH only" / "HIGH + UNVERIFIED" / "Cancel"]. Cancel → log STEP:abort and exit. Filter [TIER1_RESULTS] for Tier 2 accordingly. (Tier 1 cache is invalidated if Tier 1 produced 0 FLAGGED sources — may indicate a changed project source set; the next run will re-screen.)

**State-write (Step 5):** append to state file body:
```
### Step 5 — Source discovery
source_list_path: memory/staging/plagiarism-check-[run-id]/source-list.md
tier1_results_path: memory/staging/plagiarism-check-[run-id]/tier1-results.md
tier1_cache_used: [true/false]
scope_gate_choice: [HIGH only / HIGH + UNVERIFIED / abandoned / not applicable]
```
Update `last_completed_step: 5`.

### Step 6 — Tier 2 + structural + voice dispatch

**Tier 2 dispatch (citation-check and full-scan only):** for each source in the filtered [TIER1_RESULTS], dispatch a paired per-source agent: `PlagPerSource-A-[slug]-[run-id]` and `PlagPerSource-B-[slug]-[run-id]`, identical prompts. Each receives [PER_SOURCE_BRIEF] verbatim, [PARAGRAPH_MAP], [DRAFT_PATH], and the source page path.

**Structural pair:** dispatch `PlagStructural-A-[run-id]` and `PlagStructural-B-[run-id]`, identical prompts, both receive [STRUCTURAL_BRIEF] + [PARAGRAPH_MAP] + [DRAFT_PATH].

**Voice pair:** if voice-only mode OR (citation-check / full-scan with voice-reference enabled): determine voice reference. AskUserQuestion: "Voice reference: a corpus of the writer's previous work for comparison. Glob `pages/**/*.md` filtered by `author:: Vaidehi` returned [N] files. Confirm or provide a specific path?" Options: ["Confirmed — use these N files" / "I'll provide a specific path in Other"]. Empty → use the Glob result. If [N] is 0 and user provides no path: skip voice pair, note "Voice reference unavailable" in coverage-notes.md. Otherwise dispatch `PlagVoice-A-[run-id]` and `PlagVoice-B-[run-id]`, identical prompts, both receive [VOICE_BRIEF] + voice reference paths + [DRAFT_PATH] + [PARAGRAPH_MAP].

Append to session log: `STEP:dispatch — Agents: [list every dispatched per-source A/B + structural A/B + voice A/B]`. Dispatch all in parallel (subagent_type: `Explore`).

### Step 6.4 — Persist agent responses

After each returned agent, the **executor** Writes the agent's full response to `memory/staging/plagiarism-check-[run-id]/{agent-id}.md`.

**State-write (Step 6.4):** append to state file body:
```
### Step 6.4 — Persist agent responses
agent_outputs_dir: memory/staging/plagiarism-check-[run-id]/
agent_output_files: [list every {agent-id}.md file written this step]
```
Update `last_completed_step: 6.4`.

### Step 6.5 — Correct finding locations

Run the location-correction script over each agent's raw output (per-source agents, structural agents, voice agents — all produce findings with `Current text:` and `Location:` fields):
```
python3 .claude/scripts/correct_finding_locations.py [DRAFT_PATH] memory/staging/plagiarism-check-[run-id]/{agent-id}.md --out memory/staging/plagiarism-check-[run-id]/{agent-id}-corrected.md 2> memory/staging/plagiarism-check-[run-id]/{agent-id}-location-corrections.log
```

**Hallucination signal — explicit on-disk transformation:** for each agent, read the per-agent log file. For every `unmatched-quote:` entry, extract the quote text. Open the corresponding `{agent-id}-corrected.md` file, locate the finding whose `Current text:` equals the unmatched quote, and prepend `[QUOTE-UNMATCHED] ` to the finding's first line. Save. Step 7 synthesis treats `[QUOTE-UNMATCHED]` findings as UNVERIFIED automatically; Step 9 challenger returns DISPUTED if the quote does not appear in the draft.

**State-write (Step 6.5):** append to state file body:
```
### Step 6.5 — Correct finding locations
corrected_outputs_dir: memory/staging/plagiarism-check-[run-id]/
corrected_output_files: [list every {agent-id}-corrected.md]
location_correction_logs: [list every {agent-id}-location-corrections.log]
```
Update `last_completed_step: 6.5`.

### Step 7 — Coverage check + synthesis

**Coverage check:** all dispatched agents returned? For each missing: log re-dispatch, retry once, log failure if it fails again. Mark failed agents `Agent-failed`.

**Coverage failure notes:** record any "[Per-source <slug> / Structural / Voice] agents unavailable — [domain] findings not included" notes into `memory/staging/plagiarism-check-[run-id]/coverage-notes.md`. Step 11 reads this when filling STATUS NOTES.

**Input source for synthesis:** read each agent's **corrected** output file from `memory/staging/plagiarism-check-[run-id]/{agent-id}-corrected.md` (produced by Step 6.5 with `[QUOTE-UNMATCHED]` flags applied where applicable). The corrected files have canonical paragraph numbers and hallucination markers; the raw `{agent-id}.md` files do not. Findings prefixed with `[QUOTE-UNMATCHED]` in their `## Finding [n]` heading are treated as UNVERIFIED automatically — they bypass the both-flag-for-HIGH rule because their underlying quote is not in the draft.

**Synthesis (per `references/field-name-standard.md` match criterion):**
- Per-source pair (per slug): match findings by `Check:` value + `Current text:` (identical or substring). Source attribution comes from the agent's dispatch slug. Both flag → HIGH; one flags → UNVERIFIED. Aggregate per source.
- Structural pair: match by `Check:` value + `Current text:` (identical or substring). Both flag → HIGH; one flags → UNVERIFIED. Store as [SYNTHESISED_STRUCTURAL].
- Voice pair: match by `Pattern:` substring + `Current text:`. Both flag → HIGH; one flags → UNVERIFIED. Store as [SYNTHESISED_VOICE].

Never drop UNVERIFIED findings.

**Cross-structural/voice merge check:** for each finding in [SYNTHESISED_STRUCTURAL], compute a normalised match key (case-fold + strip whitespace) on `Current text:`. Check whether any finding in [SYNTHESISED_VOICE] has the same normalised key. Match → merge into one entry: domain = `Structural+Voice (merged)`, both concerns listed, higher severity, place under Structural section. The merge-key normalisation is necessary because structural and voice agents may quote a passage with different surrounding-context lengths; exact-string matching misses real overlaps.

**State-write (Step 7):** append to state file body:
```
### Step 7 — Synthesis
tier2_findings_path: memory/staging/plagiarism-check-[run-id]/tier2-findings.md
synthesised_structural_path: memory/staging/plagiarism-check-[run-id]/synthesised-structural.md
synthesised_voice_path: memory/staging/plagiarism-check-[run-id]/synthesised-voice.md
coverage_notes_path: memory/staging/plagiarism-check-[run-id]/coverage-notes.md
```
Update `last_completed_step: 7`.

### Step 8 — Combine findings

Combine [TIER2_FINDINGS] (per-source) + [SYNTHESISED_STRUCTURAL] + [SYNTHESISED_VOICE] into [ALL_FINDINGS], renumbered sequentially. Domain priority for presentation: Per-source → Structural → Voice → Cross-merged.

**Empty-findings guard:** if [ALL_FINDINGS] is empty, do NOT dispatch the challenger pair. Set [CHALLENGER_VERDICTS] = empty. Append to session log: `STEP:dispatch-challenger — Skipped: [ALL_FINDINGS] empty.` Skip to Step 11 (presentation agent receives empty inputs and produces a clean "no findings" report).

**State-write (Step 8):** append to state file body:
```
### Step 8 — Combine findings
all_findings_path: memory/staging/plagiarism-check-[run-id]/all-findings.md
```
Update `last_completed_step: 8`.

### Step 9 — Dispatch challenger pair

Compose challenger prompt (identical for both `PlagChallenger-A-[run-id]` and `PlagChallenger-B-[run-id]`):
```
You are the challenger agent for a plagiarism check.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type] | MODE: [mode]

PARAGRAPH MAP: [PARAGRAPH_MAP]

ALL FINDINGS FROM PRIMARY AGENTS:
[ALL_FINDINGS — each finding tagged HIGH or UNVERIFIED, sequentially numbered, reproduced in full]
[Findings flagged [QUOTE-UNMATCHED] from Step 6.5: review the quote against the draft; if it does not match any passage, return DISPUTED: quote not found in draft.]

For every finding, return one verdict. Do not silently skip — if you cannot assess one, write `## Challenger assessment: Finding [n] — NOT ASSESSED — [reason]`.

Domain-specific scope rules:
- Research essays: heavy engagement with foundational sources is expected. Close structural mirroring of a key secondary source may be unavoidable in an analytical literature review. Assess whether a structural finding represents real risk vs. discipline-standard engagement with a foundational text.
- Voice findings: assess whether voice drift reflects a genuine collapse into source register vs. appropriate adoption of disciplinary voice that the writer has internalised legitimately.
- Per-source findings: distinguish (a) close paraphrase that needs citation, (b) appropriately cited engagement that nonetheless mirrors phrasing, and (c) discipline-standard terminology that appears in many sources.

For each finding:

## Challenger assessment: Finding [n]
Domain: Per-source / Structural / Voice / Structural+Voice (merged)
Source: [slug or "n/a"]
Analysis confidence: HIGH / UNVERIFIED
Quote: "[exact text as reported by primary agent]"
[Reasoning paragraph]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question / NOT ASSESSED — reason

State reasoning first, verdict last. State the verdict label exactly once at the end.

Scope rule: assess against the draft, the source page contents, and disciplinary norms documented for THIS essay type only. Do NOT infer norms from training data for adjacent fields. If the draft says nothing about a register or the source is silent on a parallel passage, mark AMBIGUOUS: insufficient context rather than inventing norms.
```

Append to session log: `STEP:dispatch-challenger — Agents: PlagChallenger-A-[run-id], PlagChallenger-B-[run-id]`. Dispatch both in parallel (subagent_type: `Explore`).

After challengers return, the executor Writes each challenger's response to `memory/staging/plagiarism-check-[run-id]/PlagChallenger-{A,B}.md`.

**State-write (Step 9):** append to state file body:
```
### Step 9 — Dispatch challenger pair
challenger_output_files: [PlagChallenger-A-[run-id].md, PlagChallenger-B-[run-id].md]
```
Update `last_completed_step: 9`.

### Step 10 — Challenger coverage check + synthesis

Coverage check: both returned? Re-dispatch missing once each, with logged STEP:dispatch-challenger lines. Mark failures.

**Challenger synthesis:** apply the rules in `.claude/skills/plagiarism-check/references/challenger-synthesis-rules.md` (parallel to the other skills: nine verdict labels, partial- prefixes, NOT_ASSESSED handling, three orthogonal confidence axes — analysis × verdict × domain). Read the rules file in full before synthesising. Store as [CHALLENGER_VERDICTS], keyed by finding number.

**State-write (Step 10):** append to state file body:
```
### Step 10 — Challenger synthesis
challenger_verdicts_path: memory/staging/plagiarism-check-[run-id]/challenger-verdicts.md
```
Update `last_completed_step: 10`.

### Step 11 — Dispatch presentation agent

Dispatch `PlagPresentation-[run-id]` (single agent).

Before constructing the prompt: read `memory/staging/plagiarism-check-[run-id]/coverage-notes.md` from disk to fill the STATUS NOTES placeholder (empty string if no pairs failed).

Agent prompt:
```
You are the presentation agent for a plagiarism check. Output the full report inline as your response. Do NOT summarise. Every section heading and every finding entry must appear in your response output verbatim.

Read `.claude/skills/plagiarism-check/references/presentation-format.md` in full.
Read `.claude/skills/plagiarism-check/assets/report-header-template.md`.
Read [DRAFT_PATH] in full to confirm paragraph boundaries.

ESSAY TYPE: [type] | PROJECT: [PROJECT_NAME] | MODE: [mode]

PARAGRAPH MAP: [PARAGRAPH_MAP]

SYNTHESISED FINDINGS:
[ALL_FINDINGS — each tagged HIGH or UNVERIFIED, sequentially numbered, full]

CHALLENGER VERDICTS:
[CHALLENGER_VERDICTS]

STATUS NOTES (verbatim from coverage-notes.md):
[STATUS_NOTES content or empty string]

Produce the report exactly as `references/presentation-format.md` specifies. Present all findings inline. Do not truncate.
```

Append to session log: `STEP:dispatch-presentation — Agent: PlagPresentation-[run-id]`. Dispatch (subagent_type: `Explore`).

**Coverage check:** Agent returned? If missing: re-dispatch once. If fails again: executor renders output directly from [ALL_FINDINGS] + [CHALLENGER_VERDICTS] using `references/presentation-format.md`.

**On successful completion:** save the final report to `memory/staging/plagiarism-check-[run-id]/final-report.md`, update state file frontmatter `status: complete` and `last_completed_step: 11`, append the Step 11 section to the state file body with `final_report_path:`.

### Step 12 — Save on request

If the writer says "save that": copy the final report to `memory/staging/plagiarism-check-[filename]-[run-id].md`. Append to session log: `STEP:saved`.

---

## Catch-all abort rule

At ANY step, if this skill exits before logging STEP:complete: append to session log:
```
**[HH:MM:SS] SKILL:plagiarism-check RUN:[run-id] STEP:abort** — [reason]
```
Update the state file frontmatter: `status: abandoned`, `last_updated: [now]`. The state file is kept on disk so a later resume check sees it as abandoned and ignores it.

Compaction-induced exits leave `status: in-progress`. On the next /plagiarism-check invocation, Step 0 sees the in-progress state and offers Resume / Start fresh.
