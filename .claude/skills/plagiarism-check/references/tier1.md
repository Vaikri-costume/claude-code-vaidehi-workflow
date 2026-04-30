# Plagiarism Check — Tier 1 Triage Brief

Verbatim overlap triage only. Your task: determine whether each source in your batch has any verbatim phrase overlap with the draft. Do not analyse. Do not explain findings.

---

## Scope — quoted source passages only

Compare ONLY against QUOTED SOURCE PASSAGES in each source page. A quoted source passage is a line matching this pattern: text in quotation marks followed by a parenthetical citation — e.g. `"Quoted text" (citekey, p. X)` or `"Quoted text" (Author Year, p. X)`.

Do NOT compare against annotation blocks — lines containing `author::` tags (`author:: Claude`, `author:: Vaidehi`, etc.) are the writer's own notes, not source material.

---

## What to scan for

For each source: scan for any phrase of 3 or more consecutive content words (exclude function words: the, a, an, is, are, of, in, on, to, for, with, by, at, from, this, that, these, those) that appears in both the quoted source passages and the draft text.

---

## Return format

Return EXACTLY this format per source — a header block, then status on the next line:

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

Return nothing else. Do not analyse. Do not explain. Do not flag anything other than verbatim matches in quoted source passages.
