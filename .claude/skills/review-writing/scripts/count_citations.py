#!/usr/bin/env python3
"""
count_citations.py — Count Logseq page links and footnote citations per paragraph in a draft.

Usage: python3 count_citations.py <draft_file_path>
Output: JSON to stdout with per-paragraph citation inventory.

This is for research essays only. The Evidence agents receive this inventory
and focus on judgment (which paragraph claims need support) rather than counting,
which agents do unreliably over long texts.
"""
import sys
import re
import json


def count_citations_per_paragraph(text):
    paragraphs = re.split(r'\n\s*\n', text.strip())
    inventory = []
    for i, para in enumerate(paragraphs, 1):
        if not para.strip():
            continue
        # Logseq page links: [[Some Page]] or [[citekey]]
        page_links = re.findall(r'\[\[([^\]]+)\]\]', para)
        # Footnote markers: [^1], [^citekey]
        footnote_refs = re.findall(r'\[\^([^\]]+)\]', para)
        # Markdown links to source files: [text](path)
        md_links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', para)
        # Inline citations like (Author 2020) or (Author, 2020)
        inline_cites = re.findall(r'\(([A-Z][a-zA-Z]+(?:\s+(?:and|&)\s+[A-Z][a-zA-Z]+)?(?:\s+et\s+al\.?)?,?\s+\d{4}[a-z]?)\)', para)

        words = para.strip().split()
        opening = ' '.join(words[:6]) + ('...' if len(words) > 6 else '')

        total_citations = len(page_links) + len(footnote_refs) + len(md_links) + len(inline_cites)

        inventory.append({
            'paragraph': i,
            'opening_words': opening,
            'word_count': len(words),
            'citation_count': total_citations,
            'page_links': page_links,
            'footnote_refs': footnote_refs,
            'md_links': md_links,
            'inline_cites': inline_cites,
        })

    return {
        'total_paragraphs': len(inventory),
        'total_citations': sum(p['citation_count'] for p in inventory),
        'paragraphs_with_zero_citations': sum(1 for p in inventory if p['citation_count'] == 0),
        'inventory': inventory,
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: count_citations.py <draft_file>'}))
        sys.exit(1)
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    except (IOError, OSError) as e:
        print(json.dumps({'error': f'Could not read file: {e}'}))
        sys.exit(1)
    print(json.dumps(count_citations_per_paragraph(text), indent=2))
