# Proofread — Surface Brief

Delivered to surface proofreading agents (ProofSurface-A and ProofSurface-B). Run all three checks below.

---

## Check 1 — Grammar

Find: subject-verb agreement errors, article errors (a/an/the), preposition errors, tense inconsistencies within a passage, dangling modifiers. Flag each with the corrected form.

## Check 2 — Typos

Find: misspellings, duplicate words ("the the"), punctuation errors (missing full stops, double spaces, stray commas), stray characters.

## Check 3 — British spelling

Flag American variants in body text only. Do NOT flag American spelling in directly quoted source material.

Explicit list: color→colour, honor→honour, behavior→behaviour, analyze→analyse, program→programme (non-computing), catalog→catalogue, theater→theatre, recognize→recognise, practice→practise (verb), defense→defence, offense→offence, labor→labour, favor→favour, center→centre, fiber→fibre.

Systematic patterns — apply to any word not in the explicit list: -ize→-ise (organise, realise, specialise); -yze→-yse (analyse, paralyse); -or→-our (colour, favour, neighbour); -er→-re (centre, fibre, theatre, metre); -ense→-ence (defence, offence, licence as noun); -eled→-elled (travelled, cancelled, labelled); -og→-ogue (catalogue, dialogue). When uncertain: Oxford English Dictionary is the authority.

---

## Output format

Return EXACTLY this format for every finding. One entry per issue:

```
## Finding [n]
Location: paragraph [n], sentence [m] of the paragraph, [opening words of the sentence]
Current text: "[exact text as it appears in the draft]"
Proposed fix: "[corrected text]"
Check: [1 / 2 / 3]
Severity: High / Medium / Low
```

Severity guide:
- High: changes meaning, introduces ambiguity, or is clearly wrong
- Medium: non-standard but not misleading
- Low: preference-level

After all findings, append:

```
## Unrecognised terms
[Every word or phrase in the draft that is not in a standard British English dictionary: transliterated terms, domain-specific terms, words from other languages used in English prose, proper nouns specific to the subject domain (person names, place names, film titles, institution names that would not appear in a general dictionary). When in doubt, include rather than exclude — the canonical vocabulary check handles known terms. If none found: write "None identified."]

## Coverage
Check 1 (Grammar): [n] findings
Check 2 (Typos): [n] findings
Check 3 (British spelling): [n] findings
Total: [n] findings
```
