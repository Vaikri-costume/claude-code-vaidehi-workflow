#!/usr/bin/env python3
"""
extract_paragraphs.py — Produce a numbered paragraph map for a draft essay.
Usage: python extract_paragraphs.py <draft_file_path>
Output: JSON to stdout. All agents in a run receive this map and must use
these paragraph numbers — ensures consistent cross-agent paragraph references.
"""
import sys, re, json

def extract_paragraphs(text):
    paragraphs = re.split(r'\n\s*\n', text.strip())
    result = []
    para_num = 0
    for para in paragraphs:
        if not para.strip():
            continue
        para_num += 1
        words = para.strip().split()
        opening = ' '.join(words[:8]) + ('...' if len(words) > 8 else '')
        result.append({
            "paragraph": para_num,
            "opening_words": opening,
            "word_count": len(words)
        })
    return {"total_paragraphs": len(result), "paragraphs": result}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: extract_paragraphs.py <draft_file>"}))
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    print(json.dumps(extract_paragraphs(text), indent=2))
