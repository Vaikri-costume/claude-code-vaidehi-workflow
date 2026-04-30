# Challenger synthesis rules — plagiarism-check

After both PlagChallenger-A and PlagChallenger-B return, synthesise their verdicts before passing results to the presentation agent.

## Match criterion

Match by finding number — the executor numbered findings sequentially in [ALL_FINDINGS] (Step 8), and challengers reference each by `## Challenger assessment: Finding [n]`.

## Three orthogonal confidence axes (preserve all three per finding)

1. **Analysis confidence** (set by primary-pair synthesis in Step 7): `HIGH` (both primary agents flagged it) or `UNVERIFIED` (one agent flagged, the other didn't).
2. **Challenger verdict confidence** (set by this synthesis): see verdict labels below.
3. **Domain**: `Per-source` / `Structural` / `Voice` / `Structural+Voice (merged)` — and for per-source, the source slug carries through.

These axes are independent. A finding can be `(UNVERIFIED analysis, confirmed verdict, Per-source [slug])` — only one primary agent flagged it, but both challengers upheld it as a real risk.

## Verdict synthesis

For each finding, both challengers should return one of: `UPHELD`, `DISPUTED: reason`, `AMBIGUOUS: question`, or `NOT ASSESSED — reason`.

| Challenger A returned | Challenger B returned | Verdict label |
|---|---|---|
| UPHELD | UPHELD | **confirmed** |
| DISPUTED | DISPUTED | **confirmed-disputed** |
| UPHELD | DISPUTED (or vice versa) | **split** |
| AMBIGUOUS | AMBIGUOUS | **ambiguous** |
| UPHELD | AMBIGUOUS (or vice versa) | **partial-ambiguous** (lean toward upheld) |
| DISPUTED | AMBIGUOUS (or vice versa) | **partial-ambiguous** (lean toward disputed) |
| UPHELD | NOT ASSESSED | **partial-upheld** |
| DISPUTED | NOT ASSESSED | **partial-disputed** |
| NOT ASSESSED | NOT ASSESSED | **partial-unaddressed** |
| One challenger failed | UPHELD/DISPUTED/AMBIGUOUS | **partial-{verdict}** |
| Both challengers failed | n/a | **unverified-challenger** for every finding |

## Storage format

Store all verdicts as `[CHALLENGER_VERDICTS]`, one entry per finding number, with all three axes:

```
Finding 1: domain=Per-source, source=ganti2014, analysis=HIGH, verdict=confirmed
Finding 2: domain=Structural, analysis=UNVERIFIED, verdict=split
Finding 3: domain=Voice, analysis=HIGH, verdict=ambiguous
Finding 4: domain=Structural+Voice (merged), analysis=HIGH, verdict=confirmed
```

## Coverage table bucket mapping

- **upheld**: confirmed + partial-upheld
- **disputed**: confirmed-disputed + partial-disputed
- **needs your decision**: split + ambiguous + partial-ambiguous + partial-unaddressed
- **unverified-challenger**: unverified-challenger only (NOT analysis-UNVERIFIED)

## NOT_ASSESSED handling

The Step 9 challenger prompt instructs `NOT ASSESSED` as the answer when a challenger truly can't evaluate a finding. It's a deliberate non-skip. Synthesis treats it like a per-finding agent failure:
- Both challengers return NOT_ASSESSED → verdict = **partial-unaddressed**, falls into "needs your decision" bucket.
- One challenger returns NOT_ASSESSED + the other UPHELD/DISPUTED/AMBIGUOUS → treat as per-finding failure; surviving challenger's verdict becomes synthesis verdict with `partial-` prefix.
