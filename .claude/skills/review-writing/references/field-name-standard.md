# Field-name standard — review-writing

Synthesis steps in SKILL.md match findings by exact field names. If a brief is updated and a field name changes, synthesis fails silently. The deterministic location-correction script (`.claude/scripts/correct_finding_locations.py`) also relies on `Current text:` as the canonical quote-field name.

**Convention across all four writing analysis skills:** the field that holds the quoted passage from the draft is named `Current text:`. The location-correction regex is literal: `Current text: "..."`. Any brief that uses a different name (e.g. `Passage:`, `Quote:`) breaks the location-correction pipeline silently.

## Argument structure agents

```
## Finding [n]
Location: paragraph [n] — [opening words of the paragraph]
Concern: [describe the specific structural issue — one sentence]
Severity: High / Medium / Low
```

Argument findings are the one domain where exact-quote matching is unreliable because the issue is often relational (a paragraph's relationship to the surrounding argument). The location-correction script does not run on argument findings (no `Current text:` field present). Synthesis matches by `Location: paragraph [n]` AND `Concern:` substring.

## Clarity agents

```
## Finding [n]
Location: paragraph [n] — "[opening words of the sentence]"
Current text: "[exact text]"
Sub-category: [passive voice / compound sentence / unclear pronoun / jargon]
Concern: [one sentence — how this specific problem affects the reader or the argument]
Severity: High / Medium / Low
```

Match criterion: same `Sub-category:` AND `Current text:` (identical or substring).

## Evidence agents

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact quote]"
Concern: [describe the specific evidence gap — one sentence]
Severity: High / Medium / Low
```

For research essays, the brief instructs agents to consult [CITATION_INVENTORY] when assessing whether a paragraph's claims need additional support. The inventory data is not embedded in the finding — it's referenced via the `Location:` paragraph number.

Match criterion: same `Location: paragraph [n]` AND `Current text:` (identical or substring).

## Voice agents

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact quote]"
Pattern: [describe the specific voice shift — one sentence]
Concern: [what the writer's own perspective might be, if inferable]
Severity: High / Medium / Low
```

Match criterion: same `Pattern:` substring AND `Current text:` (identical or substring).

## Strengths section (every agent)

After all findings, every agent appends:
```
## Strengths
- "[exact quote 1]" — [one-sentence reason]
- "[exact quote 2]" — [one-sentence reason]
- "[exact quote 3]" — [one-sentence reason]
```

If fewer than 3 strengths apply: include only those found, do not pad.

## Challenger fields (per `references/challenger-synthesis-rules.md`)

```
## Challenger assessment: Finding [n]
Domain: Argument structure / Clarity / Evidence / Voice / Cross-domain (merged)
Analysis confidence: HIGH / UNVERIFIED
Quote: "[exact text as reported by primary agent — for argument findings without a Current text field, paraphrase the issue location instead]"
[Reasoning paragraph]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question / NOT ASSESSED — reason
```
