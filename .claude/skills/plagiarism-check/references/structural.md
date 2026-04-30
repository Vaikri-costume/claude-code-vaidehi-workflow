# Plagiarism Check — Structural Brief

Delivered to the structural agent. Run both checks below against the draft provided.

---

## Check 4 — Quote Integration

For each block quotation in the draft:
- Is there an analytical sentence **before** the quote that frames what the reader should look for?
- Is there an analytical sentence **after** the quote that extracts the specific significance for the writer's argument?
- Or does the quotation substitute for analysis?

For each embedded (inline) quotation:
- Does the surrounding sentence contain the writer's analytical claim, or does it only introduce the quotation?

**Flag: floating quotes** — quotations with no analytical framing before or after.
**Flag: argumentative substitution** — cases where the quotation IS the argument: the quote makes the writer's point, and the writer's sentence adds only "this shows that X" where X restates what the quote already says.

Do NOT flag short quotations of a technical term or proper name — only quotations of a substantial claim or description.

**Research essays:** Block quotation of 40 or more words is standard practice and is not a red flag in itself. The issue is absence of analytical framing, not quotation length. The question remains: does the block quotation replace analysis, or does it provide the evidence that the writer's surrounding sentences analyse?

---

## Check 6 — Citation Density / Source Reliance

Map which cited sources appear in which paragraphs of the draft.

**Flag when:**
- One source is cited in 4 or more consecutive paragraphs without other sources or the writer's own unanchored analytical claims appearing
- The introduction relies on the argument structure of a specific source without citing it
- The conclusion relies on the argument structure of a specific source without citing it
- The final quarter of the essay (by word count) cites only one source

In full-scan mode: also note which `type:: source` pages in the project annotation database are NOT cited anywhere in the draft. List them as "uncited sources."

Do NOT flag essays with a legitimate single-source focus (e.g., a close reading essay where one text is the primary object of analysis) — citation density is expected to be high in that case. Note the essay type in your output.

**Personal essays:** Citation density does not apply. Instead, flag over-reliance on a single anecdote or memory: if one specific personal experience is referenced or alluded to in 3 or more distinct paragraphs without the essay developing new dimensions of it, flag it. Do NOT flag an essay structured around a single central experience — only flag when repetition substitutes for development.

---

## Output format

Use this format for every finding:

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft — for Check 4: the floating quote or substitution; for Check 6: the paragraph or section where reliance begins]"
Check: [4 / 6]
Severity: RED / YELLOW / GREEN
Explanation: [one or two sentences]
```

If no findings: return exactly:
```
## No structural findings
```

## Constraints

- Do NOT write to any file
- Do NOT edit the draft file
- Return your findings only
