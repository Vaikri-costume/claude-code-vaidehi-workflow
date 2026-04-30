---
name: ai-detection-check
description: Use this skill whenever Vaidehi wants to check whether a draft essay might be flagged by AI detection tools, or whether the writing sounds too smooth, formulaic, or generic. Trigger on "check for AI detection", "does this sound like AI", "will this pass AI detection", "too polished", "too formulaic", "sounds algorithmic", "check writing authenticity", or before submitting any academic or application essay where originality of voice matters. Runs three analysis types — quantitative metrics (sentence variety, vocabulary richness, hedge density), pattern scanning (14 AI-typical constructions), and voice/texture analysis (algorithmic smoothness vs. genuine specificity).
argument-hint: "[optional: draft file path]"
---

# ai-detection-check

Checks a draft essay for AI detection risk across quantitative, pattern, and voice/texture dimensions. Domain-agnostic — works for research, personal, application, or other essay types. Three primary agent pairs (A1/A2 quantitative, B1/B2 pattern, C1/C2 voice/texture) + a dual challenger pair + a presentation agent produce the final output.

---

## Invocation

```
/ai-detection-check [optional: draft file path]
```

---

## Execution

**Mid-cycle output rule:** Show brief dispatch signals after Steps 5, 8, and 10. Allow AskUserQuestion in Steps 0, 2, 3, and 6. Do not narrate synthesis, agent results, or progress.

**Compaction survival is mandatory.** Every step persists its outputs to disk and updates `memory/staging/ai-detection-check-state-[run-id].md`. Step 0 detects in-progress state files on a new invocation and offers Resume / Start fresh. The skill cannot afford to lose 6 primary + 2 challenger + 1 presentation worth of dispatched agents to a context-window timing accident. See `.claude/references/compaction-survival.md` for the shared pattern.

### Step 0 — Resume check

Glob `memory/staging/ai-detection-check-state-*.md`. For each match read the YAML frontmatter and check `status:`.

- **None found, or all `status: complete` / `abandoned`:** continue to Step 1 with a new run_id.
- **Exactly one with `status: in-progress`:** AskUserQuestion: "Found in-progress ai-detection-check run [run-id] for [draft_path] (last completed step: [last_completed_step], updated [last_updated]). Resume or start fresh?" Options: ["Resume" / "Start fresh"].
  - **Resume:** (1) load every field from the state file's frontmatter into executor context; (2) for each section under `## Step outputs` up to `last_completed_step`, read the referenced files into the corresponding executor variables ([PARAGRAPH_MAP], [COMPUTED_METRICS], [PATTERN_PRESCAN], [SYNTHESISED_A_METRICS], [SYNTHESISED_B], [SYNTHESISED_C], [CALIBRATION], [CHALLENGER_VERDICTS], [VOCAB_REGISTER_SUGGESTION], disciplinary context block, raw agent outputs, corrected agent outputs, raw challenger outputs — whichever exist for the resume point); (3) **if `last_completed_step >= 4`, deterministically re-execute Step 4's brief-loading logic** (read `references/agent-a.md` → [AGENT_A_BRIEF]; read `references/base.md` + the appendix matching `essay_type` from frontmatter → [AGENT_BCC_BRIEF]) — briefs are not persisted to disk because they are deterministic functions of essay_type and version-controlled, but Step 8 references [AGENT_BCC_BRIEF] verbatim, so the resume protocol must reload them before skipping ahead. Append to session log: `STEP:resume — Resumed from step [last_completed_step]`. Skip to step (last_completed_step + 1).
  - **Start fresh:** rename the state file with `-abandoned-[YYYYMMDD-HHMMSS]` suffix and set `status: abandoned`. Continue with new run_id.
- **Multiple `status: in-progress`:** rare. Use AskUserQuestion to list each; user picks one to resume or "Abandon all and start fresh".

**Variable lifecycle (resume protocol — applies to all consumer steps below).** Variables produced by step N are persisted to disk via that step's State-write block. On resume, the Step 0 Resume action above is the single point that loads every persisted variable from disk into executor context — including (a) every frontmatter field, (b) every `## Step outputs` file path up to `last_completed_step`, and (c) brief content (re-read from `references/*.md` per the routing rule in Step 4 — these are deterministic and version-controlled, so re-reading on resume gives identical content). After Step 0 returns, every variable a consumer step references is in executor context. Consumer steps do NOT need per-step "Load X from disk" instructions — referring to a variable by name is sufficient.

### Step 1 — Log start

Append to `memory/staging/session-log-[YYYY-MM-DD].md`:
```
**[HH:MM:SS] SKILL:ai-detection-check RUN:[run-id] STEP:start** — Run begun.
```
Run ID is the current timestamp at second precision (e.g. `20260424-143107`).

**Create the run-state file at `memory/staging/ai-detection-check-state-[run-id].md`** with initial YAML frontmatter (`run_id`, `skill: ai-detection-check`, `last_completed_step: 1`, `status: in-progress`, `started`/`last_updated` ISO timestamps) and a `## Step outputs` body.

**State-write rule (every subsequent step):** at the end of each step, write any new variables to disk under `memory/staging/ai-detection-check-[run-id]/` and append the step's section to the state file body, then update frontmatter `last_completed_step` and `last_updated`. Without this, a compaction-induced resume cannot reconstruct variables. The full pattern is in `.claude/references/compaction-survival.md`.

### Step 2 — Load context

Check for existing context: (1) `memory/projects/project-[name].md → ## AI Detection Check Context` if a project name was provided at invocation, or (2) `memory/staging/ai-detection-check-context.md` if no project name.

**Path A — context found:**
1. Load it.
2. AskUserQuestion: "I'll use this context — [essay type, vocabulary register]. Confirm or correct." Options: ["Confirmed — proceed" / "I'll correct via Other"]. Cancel → log abort + exit.
3. If user corrects via Other: update executor + save to `memory/staging/ai-detection-check-context.md`.

**Path B — no context found:**
1. AskUserQuestion: "Essay type?" Options: ["research" / "personal" / "application" / "other"].
2. AskUserQuestion: "Domain-specific vocabulary register? (optional — 10-20 field-specific terms)." Options: ["Skip — agent will infer" / "I'll type terms in Other"]. Empty/skip → vocabulary register = "not provided".
3. Save confirmed context to `memory/staging/ai-detection-check-context.md`.

**State-write (Step 2):** update state file frontmatter with `project_name`, `project_path` (or `context_staging_path`), `essay_type`, `vocabulary_register`. Update `last_completed_step: 2` and `last_updated`.

### Step 3 — Read draft

If a file path was provided at invocation: store as [DRAFT_PATH]. Verify it exists. Not found → log abort + exit.

If pasted text was provided: save to `memory/staging/draft-[run-id].md`. Then run `python3 .claude/scripts/strip_markers.py memory/staging/draft-[run-id].md` to convert Logseq bullet-block input into paragraph-separated prose (the script preserves paragraph breaks by inserting blank lines where bullet markers stripped). If the script exits non-zero (usage error or file I/O failure): log `STEP:abort — strip_markers.py failed (exit [N])` and exit. Set [DRAFT_PATH].

If neither: AskUserQuestion: "Paste the draft text, or provide a file path." Options: ["File path" / "Paste text"] — handle the response. Cancel → abort.

**State-write (Step 3):** update state file frontmatter with `draft_path: [DRAFT_PATH]`, `input_mode: [file | paste]`. Update `last_completed_step: 3` and `last_updated`.

### Step 3.5 — Build paragraph map

```
python3 .claude/scripts/extract_paragraphs.py [DRAFT_PATH] > memory/staging/paragraphs-[run-id].json
```
Read the JSON output and store as [PARAGRAPH_MAP]. If the script exits non-zero (file not readable, usage error) or the output is `{"error": ...}`: log `STEP:abort — extract_paragraphs.py failed` and exit. Inject into every agent prompt in this run (primary, challenger, presentation). Without a shared map, two agents reading the same draft can disagree on paragraph numbering — and synthesis matching by paragraph silently produces zero matches. The map is canonical reference; the deterministic location-correction script (Step 5.5) overwrites any agent that drifts.

**State-write (Step 3.5):** the JSON output is already on disk. Append to state file body:
```
### Step 3.5 — Build paragraph map
paragraph_map_path: memory/staging/paragraphs-[run-id].json
```
Update frontmatter `last_completed_step: 3.5`.

### Step 4 — Brief composition

Brief / reference files are at `.claude/skills/ai-detection-check/references/`. Do not guess alternative paths — if any Read fails, log abort.

**[AGENT_A_BRIEF]:** Read `references/agent-a.md` in full.

**[AGENT_BCC_BRIEF]:** Read `references/base.md` in full. If essay type is **research**: also read `references/appendix-research.md` and concatenate `[base.md]\n\n---\n\n[appendix-research.md]`. If **personal / application / other**: same with `references/appendix-personal.md`.

For the field-name contract that brief outputs and synthesis matching must conform to, see `references/field-name-standard.md`. Do not rename a field in a brief without updating the standard, the location-correction script's regex, and the synthesis logic together.

**State-write (Step 4):** brief content is held in executor memory only — on resume, the executor re-reads from `references/*.md` (deterministic, version-controlled). Append marker:
```
### Step 4 — Brief composition
briefs_loaded: true
```
Update `last_completed_step: 4`.

### Step 4.5 — Pre-scans

Two scripts run before primary agents dispatch. Each replaces a search/computation problem (mechanical, exhaustive, deterministic) with the agent's real job (judgment in context).

**Quantitative metrics:**
```
python3 .claude/skills/ai-detection-check/scripts/compute_metrics.py [DRAFT_PATH] > memory/staging/metrics-[run-id].json
```
Read and store as [COMPUTED_METRICS]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — compute_metrics.py failed` and exit. Replaces sentence-counting + CV/TTR/hedge-density arithmetic that A agents would otherwise duplicate (and disagree on between runs). A agents now receive these exact values and focus on hedging-calibration judgment.

**AI pattern prescan:**
```
python3 .claude/skills/ai-detection-check/scripts/find_ai_patterns.py [DRAFT_PATH] > memory/staging/patterns-[run-id].json
```
Read and store as [PATTERN_PRESCAN]. If the script exits non-zero or output is `{"error": ...}`: log `STEP:abort — find_ai_patterns.py failed` and exit. Exact-match prescan for the 14 patterns; quoted source material is stripped before scanning so the script doesn't surface inside-quote hits to agents. B agents focus on (a) verifying each instance in context, (b) semantic equivalents not caught by exact match.

**State-write (Step 4.5):** prescan outputs are already on disk. Append to state file body:
```
### Step 4.5 — Pre-scans
computed_metrics_path: memory/staging/metrics-[run-id].json
pattern_prescan_path: memory/staging/patterns-[run-id].json
```
Update `last_completed_step: 4.5`.

### Step 5 — Dispatch primary agents

Compose six agent prompts and dispatch all in parallel.

**Agents A1 and A2 — Quantitative (identical prompts, name `AIQuant-A-[run-id]` / `AIQuant-B-[run-id]`):**
```
You are the quantitative analysis agent for an AI detection check.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]
VOCABULARY REGISTER: [list if provided, else "not provided — infer from draft"]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

COMPUTED METRICS (canonical — do not recompute):
[COMPUTED_METRICS]

These values come from a deterministic script. They are exact and authoritative. Do NOT recompute CV, TTR, or hedge density yourself. Your task is judgment, not arithmetic.

BRIEF:
[AGENT_A_BRIEF — paste full content verbatim]

Your tasks:
1. Review the COMPUTED METRICS above and confirm the severity ratings (RED / YELLOW / GREEN per metric) match what the brief's calibration says is consistent with authentic writing in this essay type and vocabulary register.

2. Propose hedging calibration: sample exactly 3 sentences from the draft — one that should hedge, one that should not, one ambiguous. Use the canonical sentence list from `sentence_inventory` in COMPUTED METRICS.

Return EXACTLY:

## Quantitative metrics review
- Sentence length CV: [value from COMPUTED_METRICS] — [RED/YELLOW/GREEN per script]; in this discipline this is [consistent / inconsistent with authentic writing] because [one sentence]
- TTR: [value] — [RED/YELLOW/GREEN]; [consistent / inconsistent] because [one sentence]
- Hedge density: [value per 100 words] — [RED/YELLOW/GREEN]; [consistent / inconsistent] because [one sentence]

## Hedging calibration proposal
Sentence A (SHOULD hedge): "[exact sentence]"
Rationale: [one sentence]

Sentence B (SHOULD NOT hedge): "[exact sentence]"
Rationale: [one sentence]

Sentence C (AMBIGUOUS): "[exact sentence]"
Rationale: [one sentence]

Disciplinary basis: [essay type] — [hedging norm].
```

**Agents B1 and B2 — Pattern scanner (identical prompts, name `AIPatterns-A-[run-id]` / `AIPatterns-B-[run-id]`):**
```
You are the pattern scanner for an AI detection check.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

EXACT-MATCH PRESCAN (deterministic, quoted source material excluded):
[PATTERN_PRESCAN]

These instances are exact phrase matches in the writer's own prose. For each: verify in context (is this instance genuinely problematic, or is the word being used in a non-pattern sense?). Then scan semantically for equivalents the prescan missed (the prescan is keyword-based; you catch rhetorical equivalents).

BRIEF:
[AGENT_BCC_BRIEF — paste full content verbatim]

For each finding (whether confirmed from prescan or newly identified semantically):

## Finding [n]
Location: paragraph [n], sentence [m], [opening words]
Current text: "[exact verbatim quote from draft]"
Pattern: [pattern number and name from base brief]
Type: exact match / semantic equivalent
Severity: RED / YELLOW / GREEN
Explanation: [one sentence — what the pattern is doing here and why it matters]

After all findings, append:
## Pattern coverage
[For each of the 14 patterns: "Pattern [n]: [n] instances found" or "Pattern [n]: no instances found"]
```

**Agents C1 and C2 — Voice/texture (identical prompts, name `AIVoice-A-[run-id]` / `AIVoice-B-[run-id]`):**
```
You are the voice and texture agent for an AI detection check.

Read [DRAFT_PATH] in full.

ESSAY TYPE: [type]

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers when reporting locations. Do not re-number paragraphs.

BRIEF:
[AGENT_BCC_BRIEF — paste full content verbatim]

Identify passages where language choices feel preemptively safe or algorithmically smooth — runs of text that wouldn't surprise a reader in any direction. Specifically:
1. Natural imperfection audit — incomplete thoughts, self-interruptions, unusual word choices, moments of genuine uncertainty.
2. Perplexity estimation — runs of 3+ sentences where every word is the most predictable option.
3. Voice texture — passages chosen to be inoffensive rather than precise.

For each finding:

## Finding [n]
Location: paragraph [n], sentence [m], [opening words]
Current text: "[exact verbatim quote from draft]"
Issue: smooth texture / missing imperfection / preemptively safe language
Severity: RED / YELLOW / GREEN
Explanation: [one sentence — what makes this passage algorithmically smooth]

Do not flag passages for being well-written. Flag only where smoothness substitutes for specificity.
```

Append to session log:
```
**[HH:MM:SS] SKILL:ai-detection-check RUN:[run-id] STEP:dispatch** — Agents: AIQuant-A-[run-id], AIQuant-B-[run-id], AIPatterns-A-[run-id], AIPatterns-B-[run-id], AIVoice-A-[run-id], AIVoice-B-[run-id]
```

Description strings must be **exactly** as named — copy verbatim. The coverage check identifies agents by description string to decide re-dispatch; if the dispatch log records one name and the coverage check looks for another, re-dispatch fails silently and the skill cannot recover from agent failures. Exactness is recovery infrastructure.

Dispatch all six in parallel (subagent_type: `Explore`).

### Step 5.4 — Persist each agent's raw response to disk

Subagents dispatched with `subagent_type: Explore` cannot use `Write` (read-only by design). After each returned agent, the **executor** Writes the agent's full response to `memory/staging/ai-detection-check-[run-id]/{agent-id}.md`. Without this persistence, Step 5.5 (location correction) and resume-after-compaction both fail — the executor's working memory of agent output is volatile; the on-disk copy isn't.

**State-write (Step 5.4):** append to state file body:
```
### Step 5.4 — Persist agent responses
agent_outputs_dir: memory/staging/ai-detection-check-[run-id]/
agent_output_files: [AIQuant-A-[run-id].md, AIQuant-B-[run-id].md, AIPatterns-A-[run-id].md, AIPatterns-B-[run-id].md, AIVoice-A-[run-id].md, AIVoice-B-[run-id].md]
```
Update `last_completed_step: 5.4`. (List the per-agent file paths explicitly so Step 0 resume knows exactly which files to load — a directory path alone is ambiguous.)

### Step 5.5 — Correct finding locations (deterministic)

Run the location-correction script over each agent's raw output before synthesis. Use a **per-agent log file** so unmatched-quote warnings can be attributed back to a specific agent — the script writes only `unmatched-quote: claimed=paraN quote=...` (no agent identifier), so a single shared log loses the agent attribution Step 5.5's hallucination handling needs:
```
python3 .claude/scripts/correct_finding_locations.py [DRAFT_PATH] memory/staging/ai-detection-check-[run-id]/{agent-id}.md --out memory/staging/ai-detection-check-[run-id]/{agent-id}-corrected.md 2> memory/staging/ai-detection-check-[run-id]/{agent-id}-location-corrections.log
```

The script extracts each finding's `Current text:` quote, searches the draft for it, and rewrites `Location: paragraph [n]` to whatever paragraph the script finds the quote in. Mismatches are corrected silently; unmatched quotes (the script cannot find the quote in the draft anywhere — a possible hallucination signal) are logged and the agent's claim is preserved.

Run the script for B and C agent outputs (A agents do not produce findings with locations to correct). After running, replace each agent's raw output with the corrected version in the executor's working set.

**State-write (Step 5.5):** append to state file body:
```
### Step 5.5 — Correct finding locations
corrected_outputs_dir: memory/staging/ai-detection-check-[run-id]/
corrected_output_files: [AIPatterns-A-[run-id]-corrected.md, AIPatterns-B-[run-id]-corrected.md, AIVoice-A-[run-id]-corrected.md, AIVoice-B-[run-id]-corrected.md]
location_correction_logs: [AIPatterns-A-[run-id]-location-corrections.log, AIPatterns-B-[run-id]-location-corrections.log, AIVoice-A-[run-id]-location-corrections.log, AIVoice-B-[run-id]-location-corrections.log]
```
Update `last_completed_step: 5.5`.

**Hallucination signal — explicit on-disk transformation:** "Flag" is not enough — the marker must be persisted on disk so Step 6 synthesis and Step 8 challenger can act on it. After running the location-correction script per agent, the agent attribution comes from the per-agent log filename, not from log line content. For each agent in {AIPatterns-A, AIPatterns-B, AIVoice-A, AIVoice-B} (Quant agents A1/A2 don't produce locatable findings), read `memory/staging/ai-detection-check-[run-id]/{agent-id}-location-corrections.log`. For every `unmatched-quote:` entry in that file, extract the quote text from the line (`unmatched-quote: claimed=paraN quote='...'`). Then open the corresponding `{agent-id}-corrected.md` file, locate the finding whose `Current text:` equals the unmatched quote, and prepend `[QUOTE-UNMATCHED] ` to that finding's first line (the `## Finding [n]` heading becomes `## Finding [n] [QUOTE-UNMATCHED]`). Save the modified file. Step 6 synthesis treats `[QUOTE-UNMATCHED]` findings as UNVERIFIED automatically (they cannot be HIGH because the underlying quote is not in the draft). Step 8 challenger receives them with the marker preserved (per the existing prompt instruction: `[Findings flagged [QUOTE-UNMATCHED] from Step 5.5: review the quote against the draft; if it does not match any passage, return DISPUTED: quote not found in draft.]`). Without this on-disk transformation, the marker exists only in executor memory and is lost on compaction. (See cross-skill bug-WHY catalogue, lesson 5 / lesson 3 / lesson 15.)

### Step 6 — Coverage check + synthesis

**Coverage check:** all six agents returned? For each missing: log re-dispatch, retry once, log failure if it fails again. Mark failed agents `Agent-failed` and continue.

**Synthesis — A pair (quantitative metrics + calibration):**

Both A agents now receive identical [COMPUTED_METRICS] from the script — they cannot disagree on the numbers themselves. Disagreement is only possible in (a) severity reasoning, (b) calibration sentence selection.

If both A returned: take [COMPUTED_METRICS] verbatim as [SYNTHESISED_A_METRICS]. For severity reasoning that diverges: use the more conservative (worse) severity and flag "agents disagree on rating".

If one A failed: use [COMPUTED_METRICS] as [SYNTHESISED_A_METRICS] but tag the surviving agent's calibration as UNVERIFIED.

If both A failed: [SYNTHESISED_A_METRICS] = [COMPUTED_METRICS] with severity ratings only (no agent reasoning). [CALIBRATION] = empty. Note in output header: "calibration unavailable — both quant agents failed; metrics shown without disciplinary commentary."

**Calibration synthesis** (between A1 and A2):
- Both agents propose the same sentence with the same label → confidence **HIGH**, auto-confirm.
- Same sentence, different labels → **CONFLICT** — write to user via Step 6 calibration gate.
- Only one agent proposes a sentence → **UNVERIFIED** — surface for confirmation.
- **Both agents propose different sentences with the same label** (e.g., A1's "SHOULD hedge" sentence ≠ A2's "SHOULD hedge" sentence) → **UNVERIFIED**: present both candidate sentences to the user via the calibration gate, ask which one (or both, or neither) is the canonical anchor for that label. This case is reachable because each agent independently selects three sentences; identical-text agreement is the exception, not the rule.

Store as [CALIBRATION] with confidence tags.

**Synthesis — B pair and C pair (per `references/field-name-standard.md` match criterion):**

Match B1 vs B2 (and C1 vs C2) findings by `Pattern:` (or `Issue:` for C) AND `Current text:` (identical or substring).
- Both agents flag the same finding → analysis confidence **HIGH**.
- Only one flags → **UNVERIFIED**.

Never drop UNVERIFIED findings. UNVERIFIED means one agent flagged it and one didn't; it may be real, the writer needs the option to judge. Dropping silently turns single-agent miss into invisible data loss.

Store as [SYNTHESISED_B] and [SYNTHESISED_C] with confidence tags. If both agents of a pair failed: that section is empty; note in output header.

**Cross-B/C merge check:**

For each finding in [SYNTHESISED_B], check whether any finding in [SYNTHESISED_C] has the same `Current text:` (identical or substring). Match → merge into one entry: type=Pattern+Voice, both `Pattern:` and `Issue:` recorded, higher severity, place under Pattern (B) section. Note "independently flagged by both pattern and voice agents — stronger signal" for presentation.

**Calibration gate:**

If [CALIBRATION] is empty: note in output header. Proceed to Step 7.

If all three calibration labels are HIGH: auto-confirm, append to session log `STEP:calibration-confirmed`, proceed.

If any CONFLICT or UNVERIFIED: AskUserQuestion presenting only the sentences that need review. Do not list HIGH-confirmed labels. For CONFLICT: show both agents' rationales, ask which label is correct. For UNVERIFIED: show proposing agent's rationale, ask user to confirm or correct. Update [CALIBRATION] from response. Cancel → abort.

**State-write (Step 6):** write [SYNTHESISED_A_METRICS], [CALIBRATION], [SYNTHESISED_B], and [SYNTHESISED_C] to disk so a compaction-induced resume can reload them. Append to state file body:
```
### Step 6 — Coverage check + synthesis
synthesised_a_metrics_path: memory/staging/ai-detection-check-[run-id]/synthesised-a-metrics.md
calibration_path: memory/staging/ai-detection-check-[run-id]/calibration.md
synthesised_b_path: memory/staging/ai-detection-check-[run-id]/synthesised-b.md
synthesised_c_path: memory/staging/ai-detection-check-[run-id]/synthesised-c.md
```
Update frontmatter `last_completed_step: 6` and `last_updated`.

### Step 7 — Compose disciplinary context block (with strict scope)

Compose plain-text block for the challenger:
```
Essay type: [X]
Vocabulary register: [list if provided / "not specified"]
Hedging norms: [paste relevant section from the appendix actually used in this run]
Calibration:
  [If [CALIBRATION] is empty: write "unavailable — both quant agents failed."]
  [Otherwise, for each calibration sentence:]
  [Sentence] — Label: [SHOULD hedge / SHOULD NOT hedge / AMBIGUOUS] — Confidence: [HIGH / UNVERIFIED] — [rationale]
  [UNVERIFIED labels were proposed by only one agent; treat as uncertain anchors.]
```

**Scope rule for the challenger (cross-skill lesson 3):** the challenger assesses against THIS context block only. It does NOT infer disciplinary norms from training data for adjacent fields not represented in the block. If the context says nothing about a register, the challenger marks the relevant finding `AMBIGUOUS: insufficient context` rather than inventing norms. Empty-result is a valid output; helpful drift produces wrong recommendations.

**State-write (Step 7):** persist the composed disciplinary context block to disk so a compaction-induced resume of Step 8 can reload it (the block is computed from [CALIBRATION] + essay-type-routed appendix + vocab register, all inline — without on-disk persistence the executor would need to re-execute Steps 4 + 6 calibration synthesis to reconstruct it). Write to `memory/staging/ai-detection-check-[run-id]/disciplinary-context.md`. Append to state file body:
```
### Step 7 — Disciplinary context block
disciplinary_context_path: memory/staging/ai-detection-check-[run-id]/disciplinary-context.md
```
Update `last_completed_step: 7`.

### Step 8 — Dispatch challenger pair

Compose challenger prompt (identical for both agents, names `AIChallenger-A-[run-id]` and `AIChallenger-B-[run-id]`):
```
You are the challenger for an AI detection check.

Read [DRAFT_PATH] in full.

PARAGRAPH MAP: [PARAGRAPH_MAP]
Use these paragraph numbers in your reasoning. Do not renumber.

ALL FINDINGS FROM PRIMARY AGENTS:
[SYNTHESISED_A_METRICS]
[SYNTHESISED_B — each finding tagged HIGH or UNVERIFIED]
[SYNTHESISED_C — each finding tagged HIGH or UNVERIFIED]
[Findings flagged [QUOTE-UNMATCHED] from Step 5.5: review the quote against the draft; if it does not match any passage, return DISPUTED: quote not found in draft.]

DISCIPLINARY CONTEXT (strict scope — see Step 7 rule):
[disciplinary context block]

BRIEF:
[AGENT_BCC_BRIEF — paste full content verbatim]

For every finding listed in ALL FINDINGS, return one verdict. Do not silently skip a finding — if you cannot assess one, write `## Challenger assessment: Finding [n] — NOT ASSESSED — [reason]`.

For each finding:

## Challenger assessment: Finding [n]
Type: Pattern / Voice & texture / Pattern+Voice / Quantitative
Analysis confidence: HIGH / UNVERIFIED
Current text: "[exact quote as reported by primary agent]"
[Reasoning paragraph — explain why this is or isn't a concern given the disciplinary context. State reasoning first.]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question

State reasoning first, verdict last. State the verdict label exactly once at the end. A label committed up front constrains the reasoning that follows; when the label comes last, the reasoning leads to the conclusion, which produces better verdicts on ambiguous findings.

For Quantitative metrics: comment on whether the metric is consistent with authentic writing in this discipline. Flag only metrics that are extreme (RED) AND inconsistent with discipline norms.

After all finding assessments, append:

## Suggested vocabulary register
List 10–20 field-specific terms inferred from this draft and its disciplinary context — terms that should appear in writing of this type and that a vocabulary register should include for future AI detection checks on similar work. Comma-separated.

## Where to save this register
Project: [infer from draft content and context]
File: `memory/projects/project-[name].md` under `## AI Detection Check Context`, field: `vocabulary_register`
If no project is known: `memory/staging/ai-detection-check-context.md`

Do NOT suggest the text is AI-generated. Do not use that framing.
```

Append to session log: `STEP:dispatch-challenger — Agents: AIChallenger-A-[run-id], AIChallenger-B-[run-id]`. Dispatch both in parallel (subagent_type: `Explore`).

After challengers return, the executor (Step 5.4 pattern) Writes each challenger's response to `memory/staging/ai-detection-check-[run-id]/AIChallenger-{A,B}.md`.

**State-write (Step 8):** append to state file body:
```
### Step 8 — Dispatch challenger pair
challenger_output_files: [AIChallenger-A-[run-id].md, AIChallenger-B-[run-id].md]
```
Update `last_completed_step: 8`.

### Step 9 — Challenger coverage check + synthesis

Coverage check: both returned? Re-dispatch missing once each, with logged STEP:dispatch-challenger lines. Mark failures.

**Challenger synthesis:** apply the rules in `.claude/skills/ai-detection-check/references/challenger-synthesis-rules.md`. The rules cover the nine verdict labels, one-failed and both-failed handling, the three orthogonal confidence axes (analysis / verdict / type), and the storage format for [CHALLENGER_VERDICTS]. Read the rules file in full before synthesising.

**Vocabulary register extraction:** use AIChallenger-A's `## Suggested vocabulary register` + `## Where to save this register`. If A produced none: use B's. If neither: [VOCAB_REGISTER_SUGGESTION] = empty.

**State-write (Step 9):** write [CHALLENGER_VERDICTS] and [VOCAB_REGISTER_SUGGESTION] to disk so a compaction-induced resume of Step 10 can reload them. Append to state file body:
```
### Step 9 — Challenger coverage check + synthesis
challenger_verdicts_path: memory/staging/ai-detection-check-[run-id]/challenger-verdicts.md
vocab_register_suggestion_path: memory/staging/ai-detection-check-[run-id]/vocab-register-suggestion.md
```
Update frontmatter `last_completed_step: 9` and `last_updated`.

### Step 10 — Dispatch presentation agent

Dispatch `AIPresentation-[run-id]` (single, subagent_type: `Explore`).

Agent prompt:
```
You are the presentation agent for an AI detection check. Output the full report inline as your response. Do NOT summarise. Do NOT describe what you produced. The executor passes your response straight to the writer — every section heading, every finding entry, every coverage row must appear in your response output verbatim.

Read `.claude/skills/ai-detection-check/references/presentation-format.md` in full — it defines the output sections, the THREE orthogonal confidence axes (analysis, challenger verdict, finding type) which must be kept visible separately per finding, the per-section selection rules, the coverage-table bucket mapping, and the rule that Location fields pass through verbatim from the synthesised findings (do not recount paragraphs).

Read `.claude/skills/ai-detection-check/assets/report-header-template.md` — use as report header, including only status notes that apply this run.

Read [DRAFT_PATH] in full to confirm paragraph context for the by-location view.

ESSAY TYPE: [type] | RUN: [run-id]

PARAGRAPH MAP: [PARAGRAPH_MAP]

QUANTITATIVE METRICS:
[SYNTHESISED_A_METRICS]

SYNTHESISED FINDINGS WITH VERDICTS:
[CHALLENGER_VERDICTS — every finding has analysis confidence + verdict confidence + type]

OUTPUT HEADER NOTES:
[Any accumulated notes: unavailable sections, sentence-count disagreement, calibration availability, partial/failed challenger.]

VOCABULARY REGISTER SUGGESTION:
[VOCAB_REGISTER_SUGGESTION — if empty, omit the Suggested vocabulary register section.]

Produce the report exactly per `references/presentation-format.md`. Output the FULL report inline as your response. The `[UNVERIFIED-CHALLENGER]` label is reserved for findings whose challenger verdict is literally `unverified-challenger`; do NOT apply it to findings whose analysis confidence is UNVERIFIED.

After the report, append to `memory/staging/session-log-[YYYY-MM-DD].md` the STEP:complete line specified at the bottom of the format file.
```

Append to session log: `STEP:dispatch-presentation — Agent: AIPresentation-[run-id]`. Dispatch.

Coverage check: agent returned? Missing → re-dispatch once. Both attempts fail → executor renders output directly from [SYNTHESISED_A_METRICS] + [CHALLENGER_VERDICTS] + [VOCAB_REGISTER_SUGGESTION] using the format file's skeleton.

**On successful completion:** save final report to `memory/staging/ai-detection-check-[run-id]/final-report.md`. Update state file `status: complete`, `last_completed_step: 10`. Append `final_report_path:` to state body.

### Step 11 — Save on request

If the user says "save that" or "save the report": copy `memory/staging/ai-detection-check-[run-id]/final-report.md` to `memory/staging/ai-detection-[run-id].md`. Append session log `STEP:saved`.

---

## Catch-all abort rule

At ANY step, if this skill exits before logging STEP:complete:

1. Append `**[HH:MM:SS] SKILL:ai-detection-check RUN:[run-id] STEP:abort** — [reason]` to session log.
2. Update state file frontmatter: `status: abandoned`, `last_updated: [now]`. The state file is kept on disk; later resume checks see it as abandoned and ignore it.

Compaction-induced exits leave `status: in-progress` (no abort handler runs). On the next invocation Step 0 sees the in-progress state and offers Resume / Start fresh — abandoned and in-progress are intentionally distinct so the writer can recover compaction-interrupted runs without manual cleanup.
