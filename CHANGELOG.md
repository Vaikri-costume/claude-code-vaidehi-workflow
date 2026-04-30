# CHANGELOG

## 2026-05-01 — Phase 7: Skill-creator framework compliance + 23-lesson convergence loop

### Writing analysis skills — all four converged

The four writing analysis skills (proofread, ai-detection-check, review-writing, plagiarism-check) brought to full skill-creator framework compliance through an 8-round trace convergence loop on the first two and template-driven 2- and 5-round loops on the last two.

**Architectural changes (all four skills):**
- YAML frontmatter (`name` + `description` + `argument-hint`) — replaces prior markdown-header format
- `briefs/` → `references/` rename — matches skill-creator convention
- `scripts/` for deterministic prescans (extract_paragraphs, strip_markers, correct_finding_locations shared; per-skill scripts where applicable)
- `assets/` for output templates (report-header-template.md)
- `references/challenger-synthesis-rules.md` — 9-value verdict taxonomy with NOT_ASSESSED handling
- `references/presentation-format.md` — output specification per skill
- `references/field-name-standard.md` — field-name contract that synthesis matching depends on
- Compaction-survival pattern — state file at `memory/staging/{skill}-state-[run-id].md` with Step 0 Resume protocol
- Variable lifecycle rule — Step 0 loads all persisted variables once; consumer steps don't restate per-step "Load X from disk"
- Three orthogonal confidence axes (analysis × challenger verdict × finding type) preserved end-to-end
- Cross-type merge rules with normalised match keys (case-fold + strip whitespace) where applicable
- Empty-pipeline guards on every challenger and presentation dispatch
- Exit-code abort guards on every script invocation
- [QUOTE-UNMATCHED] hallucination signal — explicit on-disk transformation in Step 5.5 / 6.5

### 23 cross-skill lessons captured

The convergence loop produced a numbered cross-skill bug-WHY catalogue (lessons #1–#23) that drives future skill builds:
- #1 structure-stripping must preserve structure
- #2 scripts pre-filter deterministic noise
- #3 empty-result must forbid scope drift explicitly
- #4 independent measurement axes named as such
- #5 critical values enforced deterministically not via promptcraft
- #6 agents whose response IS the output must be told so
- #7 retired in favour of #18
- #8 Glob tool vs shell-glob disambiguation
- #9 eval-mode single-agent variant
- #10 location-correction whitespace normalisation
- #11 python → python3 in script invocations
- #12 coverage-failure narrative state must be persisted as data
- #13 empty-pipeline guards on every consumer of pair-synthesis
- #14 cross-type merge keys must be normalised
- #15 "flag" is not an instruction — every flag needs an on-disk transformation
- #16 spec-vs-implementation drift in supporting reference files
- #17 synthesis tables that say "→ X" must define X's structure
- #18 state-write applies to every step that sets a frontmatter field, not only later ones
- #19 every script invocation needs explicit exit-code consumer instructions
- #20 variable lifecycle needs single authoritative declaration
- #21 convergence is asymptotic; declare it when issues are edge-cases-only
- #22 resume protocol must explicitly include deterministic re-derivations
- #23 NOT_ASSESSED is a deliberate non-skip and needs a synthesis rule

Lessons are documented in the master plan at `~/.claude/plans/tender-plotting-acorn.md` (sections "Phase 7 amendments — lessons").

### Trace round counts

- proofread: 8 rounds (12 → 8 → 9 → 7 → 4 → 3 → 1 → 4 issues)
- ai-detection-check: 8 rounds (parallel to proofread; same convergence trend)
- review-writing: 2 rounds — template validation (lesson #21)
- plagiarism-check: 5 rounds (12 → 2 → 3 → 4 → 1 issues)
- Total: 23 trace rounds across the family; ~40 issues surfaced and fixed

### Project file structure

- Created `memory/projects/project-general.md` with `## Proofread Context`, `## Global Canonical Terms`, `## Plagiarism Check Context`, `## AI Detection Check Context`, `## Review Writing Context` sections
- Appended `## Proofread Context` section to all four existing project files (project-dupatta-essay, project-dupatta-source-registry, project-vaidehi-applications, project-vaikri)

## 2026-04-28 — Phase 6: P1–P23 compliance audit

(Earlier work: 31 fixes across 4 skills derived from the P1–P23 compliance audit. Documented in the master plan.)
