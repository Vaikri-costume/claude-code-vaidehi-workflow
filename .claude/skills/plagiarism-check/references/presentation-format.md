# Presentation format — plagiarism-check

Output format for the presentation agent. The agent's response IS the report — every section heading and every finding entry must appear in the response output verbatim. Do not summarise. Do not truncate.

## Section order

1. Header (from `assets/report-header-template.md`)
2. High-severity at a glance (only if any HIGH analysis + upheld verdict findings exist)
3. By source (per-source findings grouped under each source slug)
4. Structural findings
5. Voice findings
6. Cross-merged findings (Structural+Voice)
7. Needs your decision (split + ambiguous + partial-ambiguous + partial-unaddressed)
8. Disputed (for reference)
9. Unverified findings (UNVERIFIED analysis + confirmed challenger)
10. Coverage table

Omit any section that has no qualifying findings — except the Coverage table.

## Per-section selection rules

### High severity at a glance
Findings with `analysis=HIGH` AND `verdict ∈ {confirmed, partial-upheld}` AND severity High. One line per finding: `**[Domain]** [source if per-source]: para [n]: [one-sentence summary]`. Cap at 5 entries; if more, say "N additional High findings — see By source / Structural / Voice sections."

### By source
For each source with at least one upheld finding: section heading `### Source: [slug]`. Reproduce each finding's full entry from primary agents.

### Structural findings
Group by severity High → Medium → Low. Reproduce each finding's full entry.

### Voice findings
Group by severity High → Medium → Low. Reproduce each finding's full entry.

### Cross-merged findings
Findings tagged `Structural+Voice (merged)`. Show the structural concern + voice concern + chosen severity.

### Needs your decision
Findings with verdict ∈ {split, ambiguous, partial-ambiguous, partial-unaddressed}. For split: show both challenger reasons. For ambiguous: show the challenger's question. Group by domain.

### Disputed (for reference)
Findings with verdict ∈ {confirmed-disputed, partial-disputed}. Brief one-line entries: `[Domain] [source if per-source]: "[quote excerpt]" — disputed because [reason]`.

### Unverified findings
Findings with `analysis=UNVERIFIED` AND `verdict ∈ {confirmed, partial-upheld}`. Group by domain.

---

### Coverage

```
Per-source findings (by source):
  [slug]: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
  ...
Structural findings: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Voice findings: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Cross-merged: [n] entries
Total findings: [n] upheld | [n] disputed | [n] needs your decision | [n] unverified-challenger
```

If mode is "voice-only" or "citation-check" with no sources discovered: omit the Per-source line entirely.

## After completing output

Append to session log:
```
**[HH:MM:SS] SKILL:plagiarism-check RUN:[run-id] STEP:complete** — Output presented inline. [n] upheld ([n] HIGH analysis, [n] UNVERIFIED analysis), [n] disputed, [n] needs your decision, [n] unverified-challenger.
```
