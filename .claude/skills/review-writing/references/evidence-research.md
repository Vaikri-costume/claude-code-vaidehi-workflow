# Review Writing — Evidence Integration: Research Appendix

## Agent C — Evidence integration: annotation database lookup

When a claim appears unsupported in a research essay and a project name is known, Agent C must query the annotation database:

1. Grep `pages/**/*.md` for `type:: source`
2. Read each matching file and filter to those with `project:: [[ProjectName]]`
3. For each source page, scan annotation blocks for content that could substantiate the unsupported claim
4. Report: "Paragraph [n] claims [X] without grounding — annotation from [citekey] block '[first 8 words of block]' could substantiate this."

Do NOT invent support. If no annotation matches: report the gap as unfilled — "No annotation found that substantiates this claim."

If no project is known: flag unsupported claims as "asserted without grounding — no annotation database available to check."

**Source-summary voice detection** (Agent C, research only): A specific failure mode in research essays is paragraphs that adopt a source's analytical register rather than the writer's own frame. This is distinct from Agent D's voice check — it is specifically about analysis that sounds like a summary of what one source says. Flag when:
- The paragraph's entire argument is attributable to one source's logic
- The writer's own analytical frame is absent
- The paragraph could be replaced with "(see [source])" without losing the argument

**Citation placement:** Citations should appear immediately after the specific claim they support, not at the end of a multi-claim paragraph. Flag paragraphs where a single end-of-paragraph citation appears to cover multiple distinct claims.
