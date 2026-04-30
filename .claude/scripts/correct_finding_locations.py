#!/usr/bin/env python3
"""
correct_finding_locations.py — overwrite agent-claimed paragraph numbers with
ground truth derived from the draft.

Usage: python correct_finding_locations.py <draft_file> <agent_output_file> [--out <path>]

Reads agent_output_file (a markdown file containing one or more `## Finding [n]`
blocks). For each block, extracts the `Current text:` quote and searches the
draft for it. If found, rewrites that block's `Location: paragraph [n], ...`
field to use the paragraph number from the draft. If not found, leaves the
agent's claim and emits a warning to stderr.

Why this exists: even with PARAGRAPH MAP injected into every agent prompt,
agents inconsistently use the canonical numbers. For values that drive
revision routing (paragraph numbers), promptcraft has a ceiling — deterministic
post-processing eliminates the variance entirely. See:
  /Users/vaidehi/.claude/plans/tender-plotting-acorn.md
  → "Phase 7 amendments — bug 5: critical values must be enforced deterministically"

Output: corrected agent output to stdout (or --out <path>). Stderr carries
warnings about unmatched quotes (which the calling skill should aggregate
into the session log).
"""
import sys
import re
import argparse


def split_paragraphs(text):
    """Same paragraph split rule as extract_paragraphs.py — splits on blank lines."""
    return [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]


def find_paragraph_for_quote(quote, paragraphs):
    """
    Return the 1-indexed paragraph number containing `quote`, or None.
    Tries exact match first, then a normalised-whitespace match for resilience
    against agents that re-flow whitespace inside quotes.
    """
    if not quote:
        return None
    # Exact substring
    for i, para in enumerate(paragraphs, 1):
        if quote in para:
            return i
    # Normalised whitespace
    norm_quote = re.sub(r'\s+', ' ', quote).strip()
    for i, para in enumerate(paragraphs, 1):
        norm_para = re.sub(r'\s+', ' ', para).strip()
        if norm_quote in norm_para:
            return i
    # Truncate the quote to first 40 chars and try again — agents sometimes
    # add surrounding context to a quote that doesn't appear verbatim
    if len(norm_quote) > 40:
        head = norm_quote[:40]
        for i, para in enumerate(paragraphs, 1):
            norm_para = re.sub(r'\s+', ' ', para).strip()
            if head in norm_para:
                return i
    return None


# Match a Finding block. Findings are introduced by `## Finding [n]` and end at
# the next `##` header or end-of-file.
FINDING_BLOCK_RE = re.compile(
    r'(##\s*Finding\s+\d+.*?)(?=\n##\s|\Z)',
    re.DOTALL | re.IGNORECASE
)

# Within a finding block, match the Location and Current text fields.
LOCATION_RE = re.compile(
    r'(Location:\s*paragraph\s*)(\d+)([^\n]*)',
    re.IGNORECASE
)
CURRENT_TEXT_RE = re.compile(
    r'Current text:\s*"([^"]+)"',
    re.IGNORECASE
)


def correct_block(block, paragraphs, warnings):
    """Return the block with Location's paragraph number rewritten, if a quote match was found."""
    quote_match = CURRENT_TEXT_RE.search(block)
    location_match = LOCATION_RE.search(block)
    if not (quote_match and location_match):
        return block
    quote = quote_match.group(1).strip()
    claimed = int(location_match.group(2))
    found = find_paragraph_for_quote(quote, paragraphs)
    if found is None:
        warnings.append(
            f"unmatched-quote: claimed=para{claimed} quote={quote[:60]!r}"
        )
        return block
    if found == claimed:
        return block
    # Rewrite the location number; keep everything after it intact
    new_block = LOCATION_RE.sub(
        lambda m: f"{m.group(1)}{found}{m.group(3)}",
        block,
        count=1
    )
    warnings.append(
        f"corrected: para{claimed} → para{found} for quote={quote[:60]!r}"
    )
    return new_block


def correct_agent_output(draft_text, agent_output):
    paragraphs = split_paragraphs(draft_text)
    warnings = []

    def repl(m):
        return correct_block(m.group(1), paragraphs, warnings)

    corrected = FINDING_BLOCK_RE.sub(repl, agent_output)
    return corrected, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft_file")
    ap.add_argument("agent_output_file")
    ap.add_argument("--out", help="Write corrected output to this file (default: stdout)")
    args = ap.parse_args()

    with open(args.draft_file, "r", encoding="utf-8") as f:
        draft = f.read()
    with open(args.agent_output_file, "r", encoding="utf-8") as f:
        agent_output = f.read()

    corrected, warnings = correct_agent_output(draft, agent_output)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(corrected)
    else:
        sys.stdout.write(corrected)

    for w in warnings:
        print(w, file=sys.stderr)


if __name__ == "__main__":
    main()
