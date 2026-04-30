#!/usr/bin/env python3
"""
check_british_spelling.py — Find American spelling variants in non-quoted prose.
Usage: python check_british_spelling.py <draft_file_path>
Output: JSON to stdout. Quoted material (text in "...") is excluded before scanning,
which removes the largest source of false positives — agents flagging American
spelling inside directly quoted source material.
"""
import sys, re, json

# Explicit word map: American → British
WORD_MAP = {
    "color": "colour", "colors": "colours", "colored": "coloured", "coloring": "colouring",
    "honor": "honour", "honors": "honours", "honored": "honoured", "honoring": "honouring",
    "behavior": "behaviour", "behaviors": "behaviours",
    "analyze": "analyse", "analyzes": "analyses", "analyzed": "analysed", "analyzing": "analysing",
    "program": "programme",
    "catalog": "catalogue", "catalogs": "catalogues", "cataloged": "catalogued",
    "theater": "theatre", "theaters": "theatres",
    "recognize": "recognise", "recognizes": "recognises", "recognized": "recognised",
    "practice": "practise",
    "defense": "defence", "defenses": "defences",
    "offense": "offence", "offenses": "offences",
    "labor": "labour", "labors": "labours", "labored": "laboured",
    "favor": "favour", "favors": "favours", "favored": "favoured",
    "center": "centre", "centers": "centres", "centered": "centred",
    "fiber": "fibre", "fibers": "fibres",
}

# Systematic suffix patterns (American suffix → British suffix)
SUFFIX_PATTERNS = [
    (r'\b(\w+)ize\b', r'\1ise'),
    (r'\b(\w+)ized\b', r'\1ised'),
    (r'\b(\w+)izing\b', r'\1ising'),
    (r'\b(\w+)yze\b', r'\1yse'),
    (r'\b(\w+)eled\b', r'\1elled'),
    (r'\b(\w+)eling\b', r'\1elling'),
    (r'\b(\w+)ense\b', r'\1ence'),
]

AMBIGUOUS = {"program", "practice"}

def strip_quotes(text):
    """Replace text inside "..." with spaces to exclude from scanning while preserving offsets."""
    return re.sub(r'"[^"]*"', lambda m: ' ' * len(m.group()), text)

def find_british_violations(text):
    clean_text = strip_quotes(text)
    paragraphs_raw = re.split(r'\n\s*\n', text.strip())
    paragraphs_clean = re.split(r'\n\s*\n', clean_text.strip())

    findings = []
    for para_num, (raw_para, clean_para) in enumerate(
            zip(paragraphs_raw, paragraphs_clean), 1):
        # Track positions already flagged in this paragraph to avoid double-flagging
        flagged_spans = set()

        # Check explicit word map
        for american, british in WORD_MAP.items():
            for match in re.finditer(r'\b' + re.escape(american) + r'\b',
                                     clean_para, re.IGNORECASE):
                span = (match.start(), match.end())
                flagged_spans.add(span)
                actual = clean_para[span[0]:span[1]]
                note = "verify: program (non-computing) / practice (verb)" if american in AMBIGUOUS else ""
                findings.append({
                    "paragraph": para_num,
                    "american_form": actual,
                    "british_form": british,
                    "rule": "explicit list",
                    "note": note
                })

        # Check systematic suffixes (only if not already flagged by word map)
        for american_pattern, british_replacement in SUFFIX_PATTERNS:
            for match in re.finditer(american_pattern, clean_para, re.IGNORECASE):
                span = (match.start(), match.end())
                if span in flagged_spans:
                    continue
                word = match.group(0)
                if word.lower() in WORD_MAP:
                    continue
                flagged_spans.add(span)
                british = re.sub(american_pattern, british_replacement, word, flags=re.IGNORECASE)
                findings.append({
                    "paragraph": para_num,
                    "american_form": word,
                    "british_form": british,
                    "rule": "systematic pattern",
                    "note": "verify — pattern match may have false positives"
                })

    return {"total_findings": len(findings), "findings": findings}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: check_british_spelling.py <draft_file>"}))
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    print(json.dumps(find_british_violations(text), indent=2))
