# Presentation format — ai-detection-check

The presentation agent organises all synthesised findings into a writer-facing report. Read this file and produce output exactly per the skeleton below.

**Why every finding appears inline:** Truncation is silent data loss — the writer cannot tell what was omitted unless they explicitly ask for a saved report. All findings present means the revision pass is complete on first read.

**Output the full report as the direct content of your response.** Do not summarise the report and describe what it contains. Do not paraphrase sections. The executor passes your response straight to the writer — a summary in place of the report means the writer never sees the findings.

## Three confidence axes — keep separate

Every finding carries three independent tags. Show all three explicitly per finding entry:

- **Analysis confidence**: `HIGH` (both primary agents in the B or C pair flagged the same passage) or `UNVERIFIED` (only one).
- **Challenger verdict confidence**: one of the nine values from `references/challenger-synthesis-rules.md`.
- **Finding type**: Quantitative / Pattern / Voice & texture / Pattern+Voice (cross-merged).

A finding can be `(UNVERIFIED analysis, confirmed challenger, Voice)` — strong on the challenger axis even though only one primary agent flagged it. Do not collapse axes. The `[UNVERIFIED-CHALLENGER]` label is reserved for findings whose **challenger verdict** is literally `unverified-challenger`; do NOT apply it to analysis-UNVERIFIED findings.

## Pass through location verbatim

Every finding's `Location: paragraph [n]` comes from the synthesised finding block (after the deterministic location-correction step). Use that paragraph number exactly. Do NOT recount paragraphs from the draft. The map is canonical; recounting silently misroutes the writer.

## Report skeleton

Read `assets/report-header-template.md` for the header. Then output the sections below in this order. Omit any section that has no qualifying findings.

```
[REPORT HEADER from assets/report-header-template.md]

**Note:** Statistical properties are downstream of genuine intellectual engagement. A flag means this specific language may have replaced sharper analysis — not that the text was AI-generated.

---

### Quantitative metrics
[SYNTHESISED_A_METRICS — exact values + RED/YELLOW/GREEN severity per metric. If unavailable: note that line in the header instead and omit this section.]

---

### Quick wins
[Findings with verdict=confirmed AND analysis=HIGH AND severity=RED. The clearest flags — show as one line each:
"Para [n]: [one-line description] | [Pattern/Voice]". 
Omit this section if none.]

---

### Upheld findings
[All confirmed + partial-upheld findings. Within section: HIGH analysis before UNVERIFIED; confirmed before partial-upheld.
Per-entry format:
  Para [n]: [Current text quote, ≤ 80 chars]
    Type: Pattern / Voice & texture / Pattern+Voice
    Analysis confidence: HIGH / UNVERIFIED
    Challenger verdict: confirmed / partial-upheld
    Severity: RED / YELLOW / GREEN
    Concern: [agent's one-line explanation]
  
For Pattern+Voice cross-merged findings, append: "(independently flagged by both pattern and voice agents — stronger signal)"
Omit this section if none.]

---

### Needs your decision
[split + ambiguous + partial-ambiguous + partial-unaddressed verdicts.
For split: show both challengers' verdicts and reasons.
For ambiguous / partial-ambiguous: show the challenger's specific question.
For partial-unaddressed: note "one challenger upheld; the other returned no verdict for this finding."
Omit this section if none.]

---

### Disputed findings
[confirmed-disputed + partial-disputed. Each shows challengers' reasoning briefly. Omit if none.]

---

### Unverified findings (no challenger adjudication)
[verdict=unverified-challenger findings only. NOT analysis-UNVERIFIED. Label them `[UNVERIFIED-CHALLENGER]`. Omit if none.]

---

### By location
[All upheld findings grouped by paragraph number. Para [n]: [opening words]; bulleted finding summaries with type tag. Omit if no upheld findings.]

### By type
[Pattern findings → Voice & texture findings. Within each: RED → YELLOW → GREEN. Omit a sub-section if it has no findings; omit the section if both empty.]

---

### Suggested vocabulary register
[VOCAB_REGISTER_SUGGESTION — 10–20 terms comma-separated. Then a single line: "**To persist:** save to [path from challenger] under `## AI Detection Check Context` → `vocabulary_register`."
Omit this section entirely if [VOCAB_REGISTER_SUGGESTION] is empty.]

---

### Coverage

Bucket mapping (from `references/challenger-synthesis-rules.md`):
- upheld = confirmed + partial-upheld
- disputed = confirmed-disputed + partial-disputed
- needs your decision = split + ambiguous + partial-ambiguous + partial-unaddressed
- unverified-challenger = unverified-challenger

Pattern findings: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Voice & texture findings: [n] upheld (HIGH: [n], UNVERIFIED: [n]) | [n] disputed | [n] needs your decision | [n] unverified-challenger
Quantitative metrics: [n] RED / [n] YELLOW / [n] GREEN — [calibration: confirmed | UNVERIFIED | unavailable]
Total findings: [n] upheld | [n] disputed | [n] needs your decision | [n] unverified-challenger
```

## After completing output

Append to `memory/staging/session-log-[YYYY-MM-DD].md`:

```
**[HH:MM:SS] SKILL:ai-detection-check RUN:[run-id] STEP:complete** — Output presented inline. [n] upheld ([n] HIGH analysis, [n] UNVERIFIED analysis), [n] disputed, [n] needs your decision, [n] unverified-challenger. Vocabulary register: [suggested / unavailable].
```
