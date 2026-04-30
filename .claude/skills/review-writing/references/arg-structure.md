# Review Writing — Argument Structure Brief

## Agent A — Argument Structure

A strong central claim is specific enough to be contested — it is not a description of what the essay will do, but a claim about the world that could be disputed. Each body paragraph makes one sub-claim that directly advances the central claim: not describes context, not summarises a source, but advances.

**What to look for:**
- Is the central claim stated clearly and specifically? Or is it a vague description of the essay's topic?
- Does each paragraph have a discernible sub-claim, or does it open with context, background, or quotation?
- Logical gaps: places where the reader must make an inferential leap the writer has not provided — where two adjacent claims are presented as if they follow from each other but the connection is unstated
- Floating evidence: evidence presented and then moved on from without being connected explicitly to the claim it was meant to support

**Output format:**
```
## Finding [n]
Location: paragraph [n] — [opening words of the paragraph]
Concern: [describe the specific structural issue — one sentence]
Severity: High / Medium / Low
```

Flag only the 3 most significant structural issues. If fewer than 3, flag only those found. If none, return `## No findings`.

---

## Strengths requirement

Include a `## Strengths` section at the end of your output. Minimum 2 specific strengths — quote the passage and name the move:

```
## Strengths
[n]. "[exact quoted passage]" — [one sentence: what the writing does here that works]
```

Do NOT write generic praise. If you cannot find 2 genuine strengths in your domain, note 1 and explain.

---

## Output constraints

- Do NOT write to any file
- Do NOT edit the draft
- Do NOT drop findings — if uncertain, include and mark as uncertain
- If a finding is genuinely uncertain (the issue may be intentional or discipline-appropriate): include it and mark `Severity: [level] — uncertain`. Do not omit uncertain findings.
- State the Severity field once, in the designated format field. Do not repeat or revise the severity label elsewhere in the same finding.
- If you find no problems: return `## No findings` with one sentence — do not omit
- Return ONLY what your prompt specifies
