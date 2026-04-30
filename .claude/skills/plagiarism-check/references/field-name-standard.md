# Field-name standard — plagiarism-check

Synthesis steps in SKILL.md match findings by exact field names. The deterministic location-correction script (`.claude/scripts/correct_finding_locations.py`) relies on `Current text:` as the canonical quote-field name.

**Convention across all four writing analysis skills:** the field that holds the quoted passage from the draft is named `Current text:`. The location-correction regex is literal: `Current text: "..."`.

This file documents the actual field names used in each brief's output format. The briefs are the agent's contract; the synthesis logic must conform to brief reality.

## Per-source agents (PlagPerSource-A/B per slug)

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft]"
Check: [1 / 2 / 3 / 5]
Source passage: "[relevant quoted source passage]"
Severity: RED / YELLOW / GREEN
Explanation: [one sentence]
```

The agent receives a specific source slug + path in its dispatch prompt and reports findings against that source only. The source attribution is set by the executor when dispatching `PlagPerSource-A-[slug]-[run-id]` — the slug is part of the agent identity, not a finding field.

Match criterion (within the per-source pair, A vs B for the same slug): same `Check:` value + `Current text:` (identical or substring).

## Structural agents (PlagStructural-A/B)

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft]"
Check: [4 / 6]
Severity: RED / YELLOW / GREEN
Explanation: [one or two sentences]
```

Match criterion: same `Check:` value + `Current text:` (identical or substring).

## Voice agents (PlagVoice-A/B)

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft]"
Voice reference passage: "[most analogous passage from voice reference]"
author:: tag value: "[exact tag value or 'no author tag found']"
Pattern: [describe the specific departure on one or more of: sentence-level / lexical / rhetorical / hedging register]
Severity: RED / YELLOW / GREEN
```

Match criterion: same `Pattern:` substring + `Current text:` (identical or substring).

## Tier 1 agents (PlagTier1-A/B) — per-source flag-or-clear only

Tier 1 outputs are not findings; they're per-source flag-or-clear classifications. The format (per `references/tier1.md`):
```
## Source: [slug]
File: [full file path]
FLAGGED — found: "[exact matched phrase]"
```
or
```
## Source: [slug]
File: [full file path]
CLEARED
```

Match criterion (within Tier 1 pair): same `## Source: [slug]`. Synthesis: both FLAGGED → FLAGGED-HIGH; one FLAGGED + one CLEARED → FLAGGED-UNVERIFIED (one agent missed it; safer to investigate); both CLEARED → CLEARED.

## Challenger fields (per `references/challenger-synthesis-rules.md`)

```
## Challenger assessment: Finding [n]
Domain: Per-source / Structural / Voice / Structural+Voice (merged)
Source: [slug or "n/a"]
Analysis confidence: HIGH / UNVERIFIED
Quote: "[exact text as reported by primary agent]"
[Reasoning paragraph]
Verdict: UPHELD / DISPUTED: reason / AMBIGUOUS: question / NOT ASSESSED — reason
```
