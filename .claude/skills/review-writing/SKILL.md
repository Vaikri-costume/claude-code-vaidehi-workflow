---
name: review-writing
description: Use this skill whenever Vaidehi wants a substantive analytical review of a draft — not error-checking, but feedback on argument structure, clarity, evidence integration, and voice consistency. Trigger on "review my draft", "does my argument work", "is this clear", "check my evidence", "how's the structure", "give me feedback", "what's missing", "is the voice consistent", or any request for high-level writing quality assessment. Different from /proofread (which finds errors) — this is for analytical review of the writing itself. Works for research essays, personal statements, and application essays, with criteria adapted to essay type.
argument-hint: "[optional: draft file path]"
---

# review-writing

Substantive analytical review of a draft. Four specialised agent pairs (argument structure, clarity, evidence integration, voice consistency) + dual challenger adjudication + presentation agent. Essay-type-aware: research vs personal/application/other route different evidence and voice briefs.

---

## Invocation

```
/review-writing [optional: file path or pasted text]
```

---

## Execution

**Mid-cycle output rule:** Show brief dispatch signals after Steps 5, 7, and 9. Allow AskUserQuestion in Steps 0, 2, and 3. Do not narrate synthesis or intermediate analysis.

**Compaction survival is mandatory.** Every step persists outputs to disk and updates a state file at `memory/staging/review-writing-state-[run-id].md`. Step 0 detects in-progress state files on next invocation and offers Resume / Start fresh. The writer cannot afford to lose 8 primary + 2 challenger + 1 presentation agent's worth of work to a context-window boundary. See `.claude/references/compaction-survival.md`.

### Step 0 — Resume check

Use the Glob tool to find files matching `memory/staging/review-writing-state-*.md`. For each match, read its YAML frontmatter and check `status:`.

- **None found, or all `status: complete` / `status: abandoned`:** continue to Step 1 with a new run_id.
- **Exactly one with `status: in-progress`:** AskUserQuestion: "Found an in-progress review-writing run [run-id] for [draft_path] (last completed step: [last_completed_step], updated [last_updated]). Resume or start fresh?" Options: ["Resume" / "Start fresh"].
  - **Resume:** (1) load every frontmatter field into executor context; (2) for each section under `## Step outputs` up to and including `last_completed_step`, read the referenced files into the corresponding executor variables ([PARAGRAPH_MAP], [CITATION_INVENTORY], [STRUCTURAL_FINDINGS], [CLARITY_FINDINGS], [EVIDENCE_FINDINGS], [VOICE_FINDINGS], [ALL_FINDINGS], [CHALLENGER_VERDICTS], coverage notes, raw agent outputs, corrected agent outputs, raw challenger outputs — whichever exist for the resume point); (3) **if `last_completed_step >= 4`, deterministically re-execute Step 4's brief-loading logic** (read the four brief variables per essay-type routing — briefs are not persisted to disk because they are deterministic functions of essay_type and version-controlled, but Step 5 references them verbatim, so the resume protocol must reload them before skipping ahead). Append to session log: `**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:resume** — Resumed from step [last_completed_step]`. Skip Steps 1 through `last_completed_step` and continue from step (last_completed_step + 1).
  - **Start fresh:** rename the state file to `review-writing-state-[old_run_id]-abandoned-[YYYYMMDD-HHMMSS].md` and update its frontmatter `status: abandoned`. Continue to Step 1 with a new run_id.
- **Multiple `status: in-progress` (rare; indicates prior corruption):** AskUserQuestion to list each, let the writer pick one to resume or "Abandon all and start fresh."

**Variable lifecycle (resume protocol — applies to all consumer steps below).** Variables produced by step N are persisted to disk via that step's State-write block. On resume, the Step 0 Resume action above is the single point that loads every persisted variable from disk into executor context — including (a) every frontmatter field (`project_name`, `essay_type`, `draft_path`, `filename`, `input_mode`), (b) every `## Step outputs` file path up to `last_completed_step`, and (c) brief content (re-read from `references/*.md` per the routing rule in Step 4 — these are deterministic and version-controlled, so re-reading on resume gives identical content). After Step 0 returns, every variable a consumer step references is in executor context. Consumer steps do NOT need per-step "Load X from disk" instructions.

### Step 1 — Log start

Append to `memory/staging/session-log-[YYYY-MM-DD].md`:
```
**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:start** — Run begun.
```

The run ID is the current timestamp at second precision (e.g., `20260424-143107`). Use this same ID in all subsequent log entries and agent description strings.

**Create the run-state file at `memory/staging/review-writing-state-[run-id].md`** with this initial content:
```
---
run_id: [run-id]
skill: review-writing
draft_path: (set in Step 3)
project_name: (set in Step 2)
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

**State-write rule (every subsequent step):** at the end of each step, write any new variables to disk under `memory/staging/review-writing-[run-id]/` and append the step's section to the state file body, then update frontmatter `last_completed_step` and `last_updated`.

### Step 2 — Load context

**Project name (optional):**
If a project name was provided at invocation: [PROJECT_NAME] = that value. Project-aware citation lookup is enabled for research essays.

If no project name was provided: AskUserQuestion: "Project name? (optional — enables citation lookup for research essays)" Options: ["Skip — no project" / "I'll type it in Other"]. Empty/skip → [PROJECT_NAME] = "not provided".

**Essay type:**
If essay type was provided at invocation: [type] = that value. Skip the question.

If not provided: AskUserQuestion: "Essay type?" Options: ["research" / "personal" / "application" / "other"]. Cancel → log `STEP:abort` and exit.

**State-write (Step 2):** update state file frontmatter with `project_name`, `essay_type`. Update `last_completed_step: 2` and `last_updated`.

### Step 3 — Read draft

If a file path was provided at invocation: store as [DRAFT_PATH]. Verify it exists. Not found → log abort + exit. Record [filename] (base name without extension), input_mode = "file".

If pasted text: save to `memory/staging/draft-[run-id].md`. Then run `python3 .claude/scripts/strip_markers.py memory/staging/draft-[run-id].md` to strip Logseq bullet markers in place. If the script exits non-zero: log `STEP:abort — strip_markers.py failed (exit [N])` and exit. Set [DRAFT_PATH], input_mode = "paste", [filename] = "paste".

If neither: AskUserQuestion: "Paste the draft text, or provide a file path." Options: ["File path" / "Paste text"]. Cancel → abort.

**State-write (Step 3):** update frontmatter with `draft_path`, `input_mode`, `filename`. Update `last_completed_step: 3`.

### Step 3.5 — Build paragraph map

Run:
```
python3 .claude/scripts/extract_paragraphs.py [DRAFT_PATH] > memory/staging/paragraphs-[run-id].json
```
Read the JSON output and store as [PARAGRAPH_MAP]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — extract_paragraphs.py failed` and exit. Inject into every agent prompt in this run. The map is canonical reference; the deterministic location-correction script (Step 5.5) overwrites any agent that drifts.

**State-write (Step 3.5):** append to state file body:
```
### Step 3.5 — Build paragraph map
paragraph_map_path: memory/staging/paragraphs-[run-id].json
```
Update `last_completed_step: 3.5`.

### Step 4 — Brief composition

Brief files are at `.claude/skills/review-writing/references/`. If any Read fails, log abort.

**[ARG_BRIEF]:** Read `references/arg-structure.md` in full.

**[CLARITY_BRIEF]:** Read `references/clarity.md` in full.

**[EVIDENCE_BRIEF]:** Read `references/evidence.md` in full. If essay type is **research**: also read `references/evidence-research.md` and concatenate `[evidence.md]\n\n---\n\n[evidence-research.md]`. If **personal / application / other**: same with `references/evidence-personal.md`.

**[VOICE_BRIEF]:** Read `references/voice.md` in full. If essay type is **research**: also read `references/voice-research.md` and concatenate. If **personal / application / other**: same with `references/voice-personal.md`.

For the field-name contract that brief outputs and synthesis matching must conform to, see `references/field-name-standard.md`. Do not rename a field in a brief without updating the standard, the location-correction script's regex, and the synthesis logic together.

**State-write (Step 4):** brief content is held in executor memory only — on resume, the executor re-reads from `references/*.md` (deterministic, version-controlled). Append marker:
```
### Step 4 — Brief composition
briefs_loaded: true
```
Update `last_completed_step: 4`.

### Step 4.5 — Citation inventory (research essays only)

For research essays, run:
```
python3 .claude/skills/review-writing/scripts/count_citations.py [DRAFT_PATH] > memory/staging/citations-[run-id].json
```
Read and store as [CITATION_INVENTORY]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — count_citations.py failed` and exit. Replaces per-paragraph citation counting that Evidence agents would otherwise duplicate. Evidence agents now receive the exact inventory and focus on judgment (which paragraph claims lack support) rather than counting.

For non-research essays (personal/application/other): set [CITATION_INVENTORY] = "not applicable for [type] essays". The Evidence brief for non-research essays focuses on concrete specificity, not citation density, so the inventory is unused.

**State-write (Step 4.5):** append to state file body:
```
### Step 4.5 — Citation inventory
citation_inventory_path: memory/staging/citations-[run-id].json
```
(For non-research, write `citation_inventory: "not applicable"` literally.) Update `last_completed_step: 4.5`.

### Step 5 — Dispatch primary agents

Compose eight agent prompts and dispatch all in parallel. Four domain pairs (Argument structure, Clarity, Evidence, Voice) — each pair is two agents with identical prompts.

---

**Argument structure agents `ReviewArg-A-[run-id]` and `ReviewArg-B-[run-id]` — identical prompts:**
```
You are an argument structure reviewer. Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

BRIEF:
[ARG_BRIEF — paste full content verbatim]

Your task: identify the most significant structural problems with the argument — up to 3 findings per the brief. If fewer than 3 genuine issues exist, flag only those found. Also include a `## Strengths` section per the brief's requirement (2–3 specific quoted strengths).

Return findings using the exact format in the brief. Do not group findings; one entry per issue.
```

**Clarity agents `ReviewClarity-A-[run-id]` and `ReviewClarity-B-[run-id]` — identical prompts:**
```
You are a clarity reviewer. Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

BRIEF:
[CLARITY_BRIEF — paste full content verbatim]

Your task: find clarity problems across all four sub-categories the brief defines. Also include a `## Strengths` section.

Return findings using the exact format in the brief.
```

**Evidence agents `ReviewEvidence-A-[run-id]` and `ReviewEvidence-B-[run-id]` — identical prompts:**
```
You are an evidence integration reviewer. Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]
PROJECT: [PROJECT_NAME]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations.

CITATION INVENTORY (research essays only — exact counts; for non-research this is "not applicable"):
[CITATION_INVENTORY]

For research essays, use the inventory as ground truth — do not re-count citations. Your task is to assess WHICH paragraph claims need citation support, given the counts you see.

For non-research essays, focus on concrete specificity (per the brief) — does the writer ground claims in lived experience and detail, or stay general?

BRIEF:
[EVIDENCE_BRIEF — paste full content verbatim]

Return findings using the exact format in the brief. Include a `## Strengths` section.
```

**Voice agents `ReviewVoice-A-[run-id]` and `ReviewVoice-B-[run-id]` — identical prompts:**
```
You are a voice consistency reviewer. Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations.

BRIEF:
[VOICE_BRIEF — paste full content verbatim]

Your task: find passages where the writer's analytical perspective has disappeared, where the voice has shifted inconsistently, or where the register clashes with the rest of the draft.

Return findings using the exact format in the brief. Include a `## Strengths` section.
```

---

Append to session log:
```
**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:dispatch** — Agents: ReviewArg-A-[run-id], ReviewArg-B-[run-id], ReviewClarity-A-[run-id], ReviewClarity-B-[run-id], ReviewEvidence-A-[run-id], ReviewEvidence-B-[run-id], ReviewVoice-A-[run-id], ReviewVoice-B-[run-id]
```

Description strings must be **exactly** as named — copy verbatim. The coverage check identifies agents by description string to decide re-dispatch; mismatch makes re-dispatch fail silently.

Dispatch all eight in parallel (subagent_type: `Explore`).

### Step 5.4 — Persist each agent's raw response to disk

Subagents dispatched with `subagent_type: Explore` cannot use `Write` (read-only by design). After each returned agent, the **executor** Writes the agent's full response to `memory/staging/review-writing-[run-id]/{agent-id}.md`. Without this persistence, Step 5.5 (location correction) and resume-after-compaction both fail.

**State-write (Step 5.4):** append to state file body:
```
### Step 5.4 — Persist agent responses
agent_outputs_dir: memory/staging/review-writing-[run-id]/
agent_output_files: [ReviewArg-A-[run-id].md, ReviewArg-B-[run-id].md, ReviewClarity-A-[run-id].md, ReviewClarity-B-[run-id].md, ReviewEvidence-A-[run-id].md, ReviewEvidence-B-[run-id].md, ReviewVoice-A-[run-id].md, ReviewVoice-B-[run-id].md]
```
Update `last_completed_step: 5.4`.

### Step 5.5 — Correct finding locations (deterministic)

Run the location-correction script over each agent's raw output. Use a per-agent log file so unmatched-quote warnings can be attributed back to a specific agent (the script writes only `unmatched-quote: claimed=paraN quote=...` with no agent identifier, so a single shared log loses the agent attribution):
```
python3 .claude/scripts/correct_finding_locations.py [DRAFT_PATH] memory/staging/review-writing-[run-id]/{agent-id}.md --out memory/staging/review-writing-[run-id]/{agent-id}-corrected.md 2> memory/staging/review-writing-[run-id]/{agent-id}-location-corrections.log
```

Run the script for **Clarity, Evidence, and Voice agents only** (six agents, not eight). Argument structure agents do not produce findings with a `Current text:` field — argument findings describe structural relations between paragraphs and the location-correction script's regex (`r'Current text:\s*"..."'`) would silently no-op on them. Argument findings retain the agent's claimed paragraph numbers; the [PARAGRAPH_MAP] in their prompt is the only safeguard against mis-numbering. After running, replace each Clarity/Evidence/Voice agent's raw output with the corrected version in the executor's working set.

**Hallucination signal — explicit on-disk transformation:** for each Clarity/Evidence/Voice agent (six total), read `memory/staging/review-writing-[run-id]/{agent-id}-location-corrections.log`. For every `unmatched-quote:` entry, extract the quote text. Open the corresponding `{agent-id}-corrected.md` file, locate the finding whose `Current text:` equals the unmatched quote, and prepend `[QUOTE-UNMATCHED] ` to the finding's first line. Save. Step 6 synthesis treats `[QUOTE-UNMATCHED]` findings as UNVERIFIED automatically; Step 7 challenger returns DISPUTED if the quote does not appear in the draft.

**State-write (Step 5.5):** append to state file body:
```
### Step 5.5 — Correct finding locations
corrected_outputs_dir: memory/staging/review-writing-[run-id]/
corrected_output_files: [ReviewClarity-A-[run-id]-corrected.md, ReviewClarity-B-[run-id]-corrected.md, ReviewEvidence-A-[run-id]-corrected.md, ReviewEvidence-B-[run-id]-corrected.md, ReviewVoice-A-[run-id]-corrected.md, ReviewVoice-B-[run-id]-corrected.md]
location_correction_logs: [ReviewClarity-A-[run-id]-location-corrections.log, ReviewClarity-B-[run-id]-location-corrections.log, ReviewEvidence-A-[run-id]-location-corrections.log, ReviewEvidence-B-[run-id]-location-corrections.log, ReviewVoice-A-[run-id]-location-corrections.log, ReviewVoice-B-[run-id]-location-corrections.log]
```
Update `last_completed_step: 5.5`.

### Step 6 — Coverage check + synthesis

**Coverage check:** all eight agents returned? For each missing: log re-dispatch, retry once, log failure if it fails again. Mark failed agents `Agent-failed`.

**Coverage failure notes:** record any "[Argument structure / Clarity / Evidence / Voice] agents unavailable — [domain] findings not included" notes into `memory/staging/review-writing-[run-id]/coverage-notes.md` (one per line; empty file if no pairs failed). Step 9 reads this when filling STATUS NOTES for the presentation agent.

**Synthesis — per pair (per `references/field-name-standard.md` match criterion):**

For each of the four pairs, match findings by `Location: paragraph [n]` AND quoted-text field (identical or substring).
- Both agents flag the same finding → analysis confidence **HIGH**.
- Only one flags → **UNVERIFIED**.

Never drop UNVERIFIED findings — UNVERIFIED means one agent flagged it and one didn't; it may be real, the writer needs the option to judge.

Pair outputs:
- [STRUCTURAL_FINDINGS] from Argument pair
- [CLARITY_FINDINGS] from Clarity pair
- [EVIDENCE_FINDINGS] from Evidence pair
- [VOICE_FINDINGS] from Voice pair

If both agents of a pair failed: that domain's findings = empty; note in coverage-notes.md.

**Cross-domain merge check:** for each finding in [CLARITY_FINDINGS] and [VOICE_FINDINGS], compute a normalised match key (case-fold + strip whitespace) on the quoted text. Check whether any finding in [STRUCTURAL_FINDINGS] or [EVIDENCE_FINDINGS] has the same normalised quote. Match → merge into one entry: tag domain as `Clarity+Voice` or whichever combination, list both concerns, use higher severity. The merge-key normalisation is necessary because agents in different domains may quote a passage with different surrounding-context lengths; exact-string matching misses real overlaps.

**Strengths consolidation:** collect strengths from all eight agents. Select the 2–3 most specific and distinct for inclusion (do not repeat the same passage from multiple agents).

**State-write (Step 6):** append to state file body:
```
### Step 6 — Synthesis
structural_findings_path: memory/staging/review-writing-[run-id]/structural-findings.md
clarity_findings_path: memory/staging/review-writing-[run-id]/clarity-findings.md
evidence_findings_path: memory/staging/review-writing-[run-id]/evidence-findings.md
voice_findings_path: memory/staging/review-writing-[run-id]/voice-findings.md
strengths_path: memory/staging/review-writing-[run-id]/strengths.md
coverage_notes_path: memory/staging/review-writing-[run-id]/coverage-notes.md
```
Update `last_completed_step: 6`.

### Step 7 — Dispatch challenger pair

Combine all four synthesised finding sets into [ALL_FINDINGS] (renumbered sequentially). Domain order: Argument structure → Evidence → Clarity → Voice (priority for the presentation agent).

**Empty-findings guard:** if [ALL_FINDINGS] is empty (every pair returned zero findings or both-failed), do NOT dispatch the challenger pair. Set [CHALLENGER_VERDICTS] = empty. Append to session log:
```
**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:dispatch-challenger** — Skipped: [ALL_FINDINGS] empty.
```
Skip to Step 8's State-write (records [CHALLENGER_VERDICTS] = empty), then Step 9. The presentation agent receives empty inputs and produces a clean "no findings" report.

Compose challenger prompt (identical for both `ReviewChallenger-A-[run-id]` and `ReviewChallenger-B-[run-id]`):
```
You are the challenger agent for a writing review.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers in your reasoning.

ALL FINDINGS FROM PRIMARY AGENTS:
[ALL_FINDINGS — each finding tagged HIGH or UNVERIFIED, sequentially numbered, reproduced in full]
[Findings flagged [QUOTE-UNMATCHED] from Step 5.5: review the quote against the draft; if it does not match any passage, return DISPUTED: quote not found in draft.]

For every finding, return one verdict. Do not silently skip a finding — if you cannot assess one, write `## Challenger assessment: Finding [n] — NOT ASSESSED — [reason]`.

For each finding:

## Challenger assessment: Finding [n]
Domain: Argument structure / Clarity / Evidence / Voice / Cross-domain (merged)
Analysis confidence: HIGH / UNVERIFIED
Quote: "[exact text as reported by primary agent]"
[Reasoning paragraph — explain why this is or isn't a real concern given the writer's evident analytical strategy, register, and intent for this essay type.]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question

State reasoning first, verdict last. State the verdict label exactly once at the end. A label committed up front constrains the reasoning that follows; when the label comes last, the reasoning leads to the conclusion.

Domain-specific scope rules:
- For research essays: heavy engagement with foundational sources is expected. A claim flagged as "needs more support" may be appropriately analytical rather than insufficiently grounded — assess whether the missing citation reflects a real gap or appropriate reliance on the writer's analytical voice.
- For personal/application essays: concrete specificity is the standard, not citation density. Assess concreteness, not source-coverage.
- For all essays: do NOT infer disciplinary norms from training data for fields not represented in the draft. If the draft says nothing about a register, mark relevant findings AMBIGUOUS: insufficient context rather than inventing norms.
```

Append to session log: `STEP:dispatch-challenger — Agents: ReviewChallenger-A-[run-id], ReviewChallenger-B-[run-id]`. Dispatch both in parallel (subagent_type: `Explore`).

After challengers return, the executor (Step 5.4 pattern) Writes each challenger's response to `memory/staging/review-writing-[run-id]/ReviewChallenger-{A,B}.md`.

**State-write (Step 7):** append to state file body:
```
### Step 7 — Dispatch challenger pair
all_findings_path: memory/staging/review-writing-[run-id]/all-findings.md
challenger_output_files: [ReviewChallenger-A-[run-id].md, ReviewChallenger-B-[run-id].md]
```
Update `last_completed_step: 7`.

### Step 8 — Challenger coverage check + synthesis

Coverage check: both returned? Re-dispatch missing once each, with logged STEP:dispatch-challenger lines. Mark failures.

**Challenger synthesis:** apply the rules in `.claude/skills/review-writing/references/challenger-synthesis-rules.md` (parallel to proofread/AIDC's rules: nine verdict labels, one-failed and both-failed handling, NOT_ASSESSED handling, three orthogonal confidence axes — analysis × verdict × domain, and the storage format for [CHALLENGER_VERDICTS]). Read the rules file in full before synthesising.

Store as [CHALLENGER_VERDICTS], keyed by finding number.

**State-write (Step 8):** append to state file body:
```
### Step 8 — Challenger coverage + synthesis
challenger_verdicts_path: memory/staging/review-writing-[run-id]/challenger-verdicts.md
```
Update `last_completed_step: 8`.

### Step 9 — Dispatch presentation agent

Dispatch `ReviewPresentation-[run-id]` (single agent — presentation is deterministic organisation, paired redundancy adds no value).

Before constructing the prompt: read `memory/staging/review-writing-[run-id]/coverage-notes.md` from disk to fill the STATUS NOTES placeholder (empty string if no pairs failed).

Agent prompt:
```
You are the presentation agent for a writing review. Output the full report inline as your response. Do NOT summarise. The executor passes your response straight to the writer — every section heading, every finding entry, every coverage row must appear in your response output verbatim.

Read `.claude/skills/review-writing/references/presentation-format.md` in full — it defines the output sections, per-section selection rules, and coverage-table bucket mapping.

Read `.claude/skills/review-writing/assets/report-header-template.md` — use it as the header.

Read [DRAFT_PATH] in full to confirm paragraph boundaries for the by-location view.

ESSAY TYPE: [type] | PROJECT: [PROJECT_NAME]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Every finding's `Location:` field already references this map.

SYNTHESISED FINDINGS:
[ALL_FINDINGS — each finding tagged HIGH or UNVERIFIED, sequentially numbered, reproduced in full]

CHALLENGER VERDICTS:
[CHALLENGER_VERDICTS — one line per finding number per challenger-synthesis-rules.md]

STRENGTHS:
[STRENGTHS — 2–3 selected strengths from primary agents]

STATUS NOTES (for the header — pass through verbatim):
[Coverage failure notes from coverage-notes.md, or empty string if no pairs failed]

Produce the report exactly as `references/presentation-format.md` specifies. Present all findings inline. Do not truncate.
```

Append to session log: `STEP:dispatch-presentation — Agent: ReviewPresentation-[run-id]`. Dispatch (subagent_type: `Explore`).

**Coverage check:** Agent returned? If missing: re-dispatch once with logged STEP:dispatch-presentation. If fails again: executor renders output directly from [ALL_FINDINGS] + [CHALLENGER_VERDICTS] using `references/presentation-format.md`, then appends STEP:complete to session log.

**On successful completion:** save the final report text to `memory/staging/review-writing-[run-id]/final-report.md`, update state file frontmatter `status: complete` and `last_completed_step: 9`, append the Step 9 section to the state file body with `final_report_path:`.

### Step 10 — Save on request

If the writer says "save that" or "save the report": copy `memory/staging/review-writing-[run-id]/final-report.md` to `memory/staging/review-writing-[filename]-[run-id].md`, where [filename] is the base filename or "paste". Append to session log: `STEP:saved`.

---

## Catch-all abort rule

At ANY step, if this skill exits before logging STEP:complete: append to session log:
```
**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:abort** — [reason]
```
Update the state file frontmatter: `status: abandoned`, `last_updated: [now]`. The state file is kept on disk so a later resume check sees it as abandoned (not in-progress) and ignores it.

Compaction-induced exits leave `status: in-progress` (no abort handler runs). On the next /review-writing invocation, Step 0 sees the in-progress state and offers Resume / Start fresh — abandoned and in-progress are intentionally distinct.
