# Presentation format — review-writing

Output format for the presentation agent. The agent's response is the report — every section heading and every finding entry must appear in the response output verbatim. Do not summarise. Do not truncate.

## Section order

1. Header (from `assets/report-header-template.md`)
2. High-severity at a glance (only if any HIGH analysis + upheld verdict findings exist)
3. Observed strengths
4. By location (paragraph-grouped view)
5. By domain (Argument → Evidence → Clarity → Voice)
6. Needs your decision (split + ambiguous + partial-ambiguous + partial-unaddressed)
7. Disputed (for reference)
8. Unverified findings (UNVERIFIED analysis confidence + confirmed challenger — actionable but single-agent)
9. Coverage table

Omit any section that has no qualifying findings (do not show empty headings) — except the Coverage table, which always appears.

## Per-section selection rules

### High severity at a glance
Findings with `analysis=HIGH` AND `verdict ∈ {confirmed, partial-upheld}` AND severity High. One line per finding: `**[Domain]** para [n]: [one-sentence summary]`. Cap at 5 entries; if more, say "N additional High findings — see By domain section."

### Observed strengths
2–3 specific quoted strengths from primary agents (selected during Step 6 synthesis). Show each as `> "[quote]"` followed by `— [Domain agent]: [why this works]`.

### By location
For each paragraph that contains at least one upheld finding, list the findings:
```
**Para [n]: "[opening words…]"**
- [Domain] | [confidence pair: HIGH/UNVERIFIED + verdict] | [one-line finding summary]
```

### By domain
Sections in priority order: Argument structure → Evidence → Clarity → Voice → Cross-domain (merged). Within each domain, order by severity High → Medium → Low; within severity, confirmed before partial-upheld; within verdict, HIGH analysis before UNVERIFIED. Reproduce each finding's full entry from primary agents (don't paraphrase).

### Needs your decision
All findings with verdict ∈ {split, ambiguous, partial-ambiguous, partial-unaddressed}. For split: show both challenger reasons. For ambiguous: show the question the challenger raised. Group by domain.

### Disputed (for reference)
Findings with verdict ∈ {confirmed-disputed, partial-disputed}. Brief one-line entries: `[Domain] para [n]: "[quote excerpt]" — disputed because [reason]`.

### Unverified findings
Findings with `analysis=UNVERIFIED` AND `verdict ∈ {confirmed, partial-upheld}`. These are the dual-pair architecture's signal-improvement case (one primary agent missed it, both challengers caught it as real). Group by domain.

---

### Coverage

Bucket mapping (from `references/challenger-synthesis-rules.md`):
- upheld = confirmed + partial-upheld
- disputed = confirmed-disputed + partial-disputed
- needs your decision = split + ambiguous + partial-ambiguous + partial-unaddressed
- unverified-challenger = unverified-challenger

```
Argument structure: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Evidence: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Clarity: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Voice: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Cross-domain (merged): [n] entries
Total findings: [n] upheld | [n] disputed | [n] needs your decision | [n] unverified-challenger
```

## After completing output

Append to session log:
```
**[HH:MM:SS] SKILL:review-writing RUN:[run-id] STEP:complete** — Output presented inline. [n] upheld ([n] HIGH analysis, [n] UNVERIFIED analysis), [n] disputed, [n] needs your decision, [n] unverified-challenger.
```
