# Field-name standard — ai-detection-check

Synthesis steps in SKILL.md match findings by exact field names. If a brief is updated and a field name changes silently, synthesis fails silently — findings become UNVERIFIED or unmatched without any error. The deterministic location-correction script (`.claude/scripts/correct_finding_locations.py`) also relies on `Current text:` as the canonical quote-field name. Brief files and SKILL.md must conform to the names below.

**Convention across all four writing analysis skills:** the field that holds the quoted passage from the draft is named `Current text:`. ai-detection-check historically used `Passage (from draft):` — that name is **deprecated**; new agent prompts and brief outputs use `Current text:` so the location-correction script and cross-skill synthesis logic work without skill-specific branching.

## Quantitative agents (A1, A2)

The sentence inventory and the raw metric values are **provided deterministically by `scripts/compute_metrics.py`** (`sentence_inventory`, `cv`, `ttr`, `hedge_density` fields in [COMPUTED_METRICS]). Agents do NOT re-output a `## Sentence inventory` section — they consume the inventory from COMPUTED METRICS. The agent's own output begins at `## Quantitative metrics review` (matching SKILL.md Step 5).

```
## Quantitative metrics review
- Sentence length CV: [value from COMPUTED_METRICS] — RED / YELLOW / GREEN — [agent's reasoning on whether the rating is consistent with this essay type]
- TTR (first 500 words): [value] — RED / YELLOW / GREEN — [reasoning]
- Hedge density: [value] per 100 words — RED / YELLOW / GREEN — [reasoning]

## Hedging calibration proposal
Sentence A (SHOULD hedge): "[exact sentence from draft]"
Rationale: [one sentence]

Sentence B (SHOULD NOT hedge): "[exact sentence from draft]"
Rationale: [one sentence]

Sentence C (AMBIGUOUS): "[exact sentence from draft]"
Rationale: [one sentence]

Disciplinary basis: [essay type] — [hedging norm]
```

Match criterion (synthesis A1 vs A2): same sentence count → metrics confirmable; same sentence text in calibration proposal → label match.

## Pattern agents (B1, B2)

```
## Finding [n]
Location: paragraph [n], sentence [m], [opening words]
Current text: "[exact verbatim quote from draft]"
Pattern: [pattern number and name from base brief]
Type: exact match / semantic equivalent
Severity: RED / YELLOW / GREEN
Explanation: [one sentence — what the pattern is doing here and why it matters]
```

Match criterion (B1 vs B2): same `Pattern:` value AND `Current text:` (identical or substring).

After all findings, append `## Pattern coverage` summarising counts per pattern.

## Voice & texture agents (C1, C2)

```
## Finding [n]
Location: paragraph [n], sentence [m], [opening words]
Current text: "[exact verbatim quote from draft]"
Issue: smooth texture / missing imperfection / preemptively safe language
Severity: RED / YELLOW / GREEN
Explanation: [one sentence — what makes this passage algorithmically smooth]
```

Match criterion (C1 vs C2): same `Issue:` value AND `Current text:` (identical or substring).

## Cross-B/C merge

When a B finding and a C finding share the same `Current text:` (identical or substring), merge into a compound finding. Place under Pattern (B) section. Add `Pattern+Voice` to the type axis. Use higher severity. Record both `Pattern:` and `Issue:` values in the merged entry.

## Challenger agents (AIChallenger-A, AIChallenger-B)

```
## Challenger assessment: Finding [n]
Type: Pattern / Voice & texture / Pattern+Voice / Quantitative
Analysis confidence: HIGH / UNVERIFIED
Current text: "[exact quote as reported by primary agent]"
[Reasoning paragraph]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question
```

Match criterion (synthesis A vs B challenger): same Finding number.

## Why field names are versioned here

Renaming `Current text:` to `Passage:` in a brief without updating SKILL.md synthesis logic and the location-correction script would produce a silent failure: synthesis matches by exact field text, the script's regex looks for `Current text:` — both stop matching, every finding becomes UNVERIFIED or unmatched, but the skill still runs and still produces a report. Treating field names as a contract prevents that.
