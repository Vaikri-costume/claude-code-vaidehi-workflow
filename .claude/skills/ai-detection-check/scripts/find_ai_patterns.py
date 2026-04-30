#!/usr/bin/env python3
"""
find_ai_patterns.py — Exact-match prescan for AI detection patterns.
Usage: python find_ai_patterns.py <draft_file_path>
Output: JSON to stdout.

Per cross-skill lesson #2 from proofread (scripts pre-filter deterministic noise),
this scan EXCLUDES patterns appearing inside directly quoted source material —
"..." regions are masked before scanning. The B (pattern) agents receive the
remaining real-prose hits and focus on context-judgment + semantic equivalents,
not re-doing the keyword search.
"""
import sys, re, json

PATTERNS = {
    1: {"name": "Significance inflation", "phrases": [
        "groundbreaking", "revolutionary", "transformative", "unprecedented",
        "paradigm shift", "seminal", "pivotal contribution"]},
    2: {"name": "Hollow generalisations", "phrases": [
        "throughout history", "in today's world", "society has always",
        "since time immemorial", "across cultures"]},
    3: {"name": "False-balance framing", "phrases": [
        "while some argue", "there are those who believe",
        "this essay will examine both sides", "on one hand", "on the other hand"]},
    4: {"name": "Unearned conclusions", "phrases": [
        "this shows the importance of", "further research is needed",
        "ultimately, this reveals the complexity",
        "it is clear that more work must be done"]},
    5: {"name": "AI vocabulary cluster", "phrases": [
        "delve", "intricate", "tapestry", "nuanced tapestry", "navigate",
        "landscape", "realm", "comprehensive", "robust", "multifaceted",
        "multitude", "crucially", "pivotal"]},
    6: {"name": "Copula avoidance", "phrases": [
        "serves as", "functions as", "operates as", "proves to be",
        "emerges as", "comes to represent"]},
    7: {"name": "Vague attributions", "phrases": [
        "experts say", "scholars note", "research suggests",
        "studies show", "critics argue", "many have observed"]},
    8: {"name": "Promotional lexicon", "phrases": [
        "powerful", "striking", "compelling", "rich", "innovative",
        "fascinating", "remarkable", "eloquent", "insightful"]},
    9: {"name": "Excessive hedging", "phrases": [
        "it could be argued that", "it might be suggested that",
        "one could possibly say", "this may indicate",
        "it would seem that", "it appears as though"]},
    10: {"name": "Negative parallelisms", "phrases": [
        "not only", "not merely", "not simply"]},
    11: {"name": "Rule of three (triadic lists)", "phrases": [],
         "structural": True,
         "note": "Triadic lists ('X, Y, and Z' / 'X, Y, Z' parallel constructions) are structural, not exact-phrase. The script reports exact-match count = 0; the agent must scan semantically for triplet patterns where the rhetorical effect substitutes for specificity (e.g. 'embroidery, weaving, and dyeing techniques' is content-bearing; 'compelling, powerful, and transformative' is filler triadic lift)."},
    12: {"name": "Uniform sentence length", "phrases": [],
         "structural": True,
         "note": "Detected via the CV metric in compute_metrics.py (sentence_length_cv < 0.30 → RED). The script reports exact-match count = 0 here; severity for this pattern is set by the CV rating, not by phrase scanning. Agents should reference [COMPUTED_METRICS].cv_rating when reporting Pattern 12 in the coverage table."},
    13: {"name": "Filler openings", "phrases": [
        "it is worth noting that", "it is important to recognise that",
        "it should be noted that", "one must consider", "it bears mentioning that"]},
    14: {"name": "Announcement sentences", "phrases": [
        "this essay will examine", "in this section, i will discuss",
        "having established", "i now turn to", "this paper argues that"]},
}


def strip_quoted(text):
    """Replace text inside "..." with spaces so positions are preserved but
    quoted source material is excluded from pattern scanning."""
    return re.sub(r'"[^"]*"', lambda m: ' ' * len(m.group()), text)


def find_patterns(text):
    clean_text = strip_quoted(text)
    text_lower = clean_text.lower()
    results = {}
    for pattern_num, pattern in PATTERNS.items():
        instances = []
        for phrase in pattern["phrases"]:
            for match in re.finditer(re.escape(phrase), text_lower):
                start = max(0, match.start() - 40)
                end = min(len(clean_text), match.end() + 40)
                # Pull context from the original (un-masked) text, since position
                # is preserved by the space-fill in strip_quoted.
                context = text[start:end].replace('\n', ' ')
                instances.append({
                    "phrase": phrase,
                    "context": f"...{context}...",
                })
        results[str(pattern_num)] = {
            "name": pattern["name"],
            "exact_match_count": len(instances),
            "instances": instances,
        }
    return {
        "patterns": results,
        "total_exact_matches": sum(r["exact_match_count"] for r in results.values()),
        "note": "Inside-quoted-material patterns are excluded from this scan.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: find_ai_patterns.py <draft_file>"}))
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    print(json.dumps(find_patterns(text), indent=2))
