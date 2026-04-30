# Plagiarism Check — Per-Source Brief

Delivered to per-source analysis agents. Run all checks below against the source and draft provided.

---

## Check 1 — Direct Overlap

**Scope: quoted source passages only.**

A quoted source passage is a line in the source page matching this pattern: text in quotation marks followed by a parenthetical citation — e.g. `"Quoted text" (citekey, p. X)` or `"Quoted text" (Author Year, p. X)`.

Do NOT compare against annotation blocks — lines containing `author::` tags (`author:: Claude`, `author:: Vaidehi`, etc.) are the writer's own analytical notes, not source material. Overlap between the draft and annotation notes is expected and is not plagiarism.

Find verbatim phrases of 3 or more consecutive content words (exclude function words: the, a, an, is, are, of, in, on, to, for, with, by, at, from, this, that, these, those) that appear in both quoted source passages and the draft text.

Flag all verbatim matches regardless of length — there is no acceptable-length threshold for unmarked quotation.

Do NOT flag single words or function words. Do NOT flag field-standard technical terms that are the only possible way to name the concept — but if uncertain whether a term is field-standard, flag it and note the uncertainty.

---

## Check 2 — Synthesis vs Summary

Has the writer's analytical voice transformed the source material, or are they summarising it?

**Markers of summary (flag):**
- Chronological or sequential recounting of the source's own argument structure
- Heavy reliance on "X argues that...", "X shows that...", "According to X..." without the writer's own analytical frame added
- Paragraphs where the source's logic drives the paragraph, not the writer's claim
- The writer's contribution is to report what the source says, not to use the source to support a claim

**Markers of synthesis (retain):**
- The source is used to support a claim that is the writer's own
- The source is assembled alongside other perspectives into a new argument
- The writer's analytical voice is present: they extend, complicate, apply, or dispute the source's logic

For each flagged passage: quote the draft passage, identify the specific summary pattern, suggest what synthesis would look like in that context.

Do NOT flag passages where the writer has clearly transformed the source's argument into their own analytical frame.

---

## Check 3 — Analytical Framework Origin

Has the writer adopted this source's theoretical or analytical framework without attribution?

**What to look for:**
- Key theoretical terms specific to this source appearing in the draft without citation
- The same organisational or argumentative logic as this source's structure — same steps, same sequence, same categories
- The writer's central analytical lens tracing directly to this source without acknowledgment

**When to flag:**
- The framework is used WITHOUT any attribution to this source AND is central to the draft's argument

**When to retain:**
- The source is cited elsewhere in the draft even if not in the specific passage using the framework
- The framework is so widely used in the field that it is no longer attributed to an individual source
- Only minor vocabulary is shared

Do NOT flag framework use that is properly attributed, even briefly.

---

## Check 5 — Paraphrase Distance

Compare annotated passages from this source to corresponding passages in the draft.

**Near-paraphrase (flag when all three conditions hold):**
1. The sentence structure is identical or near-identical (same grammatical pattern, same number of clauses)
2. Word choice is changed to synonyms but the sequence of ideas is identical to the source
3. The paraphrased passage appears in the same argumentative position as the source passage

**Retain when:**
- Only the key claim or term is borrowed (unavoidable when engaging with a specific argument) AND the sentence is otherwise the writer's own construction
- The writer has changed the argumentative position, direction, or logical relationship of the claim

For each flagged passage: show the source passage and the draft passage side by side; identify which of the three conditions hold.

---

## Output format

Use this format for every finding:

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft]"
Check: [1 / 2 / 3 / 5]
Source passage: "[relevant quoted source passage — must be from quoted source text, not an annotation block]"
Severity: RED / YELLOW / GREEN
Explanation: [one sentence]
```

If no findings: return exactly:
```
## No findings for [slug]
```

Do not omit this line — omission cannot be distinguished from agent failure.

## Constraints

- Do NOT write to any file
- Do NOT edit the draft or source files
- Do NOT drop findings — if uncertain, keep and mark as uncertain
- Return all findings
