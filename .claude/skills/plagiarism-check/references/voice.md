# Plagiarism Check — Voice Brief

Delivered to the voice-comparison agent. Run the voice comparison check below.

---

## Check 7 — Voice Comparison

Compare draft passages against the voice reference on four dimensions:

**1. Sentence-level:** What are the characteristic sentence-opening patterns in the voice reference? First-person analytical frames ("I argue", "my reading suggests", "I want to suggest"), direct assertions without hedging, or something else? Does the draft use different patterns?

**2. Lexical:** What domain-specific vocabulary and characteristic qualifiers appear in the voice reference? What idiomatic phrases does the writer use? Are these present or absent in the draft?

**3. Rhetorical:** How does the writer introduce claims in the voice reference — with what move? How do they introduce evidence — directly or after framing? How do they close paragraphs? Does the draft follow these patterns?

**4. Hedging register:** Does the voice reference hedge interpretive claims? At what level? Does the draft hedge more heavily, more lightly, or differently?

For each flagged passage:
- Quote the draft passage
- Quote the most analogous passage from the voice reference
- Describe the specific departure on one or more of the four dimensions above

For every annotation block used as voice reference: output the block text AND the `author::` tag value exactly as it appears. Do NOT assume the tag is correct — display it as-is. If the voice reference has no `author::` tag: note "no author tag found."

Do NOT flag passages where the draft matches the dominant voice of the reference. Only flag departures.

---

## Output format

Use this format for every finding:

```
## Finding [n]
Location: paragraph [n] — "[opening words of the passage]"
Current text: "[exact verbatim quote from draft]"
Voice reference passage: "[most analogous passage from voice reference]"
author:: tag value: "[exact tag value as it appears in the source, or 'no author tag found']"
Pattern: [describe the specific departure on one or more of the four dimensions: sentence-level / lexical / rhetorical / hedging register]
Severity: RED / YELLOW / GREEN
```

If no findings: return exactly:
```
## No voice findings
```

If no voice reference was provided (the prompt will explicitly state this): return exactly:
```
## No voice reference provided — Check 7 skipped
```
(This is a distinct case from "no findings" — the check was not run, not run and found nothing.)

## Constraints

- Do NOT write to any file
- Do NOT edit the draft or reference files
- Return your findings only
