#!/usr/bin/env python3
"""
compute_metrics.py — AI detection quantitative metrics for a draft essay.
Usage: python compute_metrics.py <draft_file_path>
Output: JSON to stdout.

Produces the same numbers two A-quant agents would otherwise compute manually
(sentence inventory, CV, TTR, hedge density), so primary agents focus on
hedging-calibration judgment rather than re-doing arithmetic that varies
between runs. See:
  /Users/vaidehi/.claude/plans/tender-plotting-acorn.md
  → "Phase 7 amendments — bug 5: critical values must be enforced deterministically"
"""
import sys, re, json, math


def compute_metrics(text):
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'(])', text.strip())
    sentences = [s for s in sentences if s.strip()]
    word_counts = [len(s.split()) for s in sentences]
    n = len(word_counts)
    if n == 0:
        return {"error": "No sentences found"}

    mean = sum(word_counts) / n
    stdev = math.sqrt(sum((x - mean) ** 2 for x in word_counts) / n)
    cv = round(stdev / mean, 3) if mean > 0 else 0

    all_words = text.lower().split()
    first_500 = all_words[:500]
    ttr = round(len(set(first_500)) / len(first_500), 3) if first_500 else 0

    hedge_patterns = [
        r'\bcould\b', r'\bmight\b', r'\bmay\b', r'\bperhaps\b',
        r'\bpossibly\b', r'\bit seems\b', r'\bit appears\b',
        r'\bone might argue\b', r'\bit could be argued\b',
        r'\bappears to\b', r'\bseems to\b', r'\bsuggests\b', r'\blikely\b',
    ]
    total_words = len(all_words)
    hedge_count = sum(len(re.findall(p, text.lower())) for p in hedge_patterns)
    hedge_density = round(hedge_count / total_words * 100, 2) if total_words > 0 else 0

    sentence_inventory = [
        {"index": i + 1, "word_count": wc, "sentence": sent}
        for i, (sent, wc) in enumerate(zip(sentences, word_counts))
    ]

    return {
        "sentence_count": n,
        "sentence_inventory": sentence_inventory,
        "mean_length": round(mean, 2),
        "stdev_length": round(stdev, 2),
        "cv": cv,
        "cv_rating": "RED" if cv < 0.30 else "YELLOW" if cv < 0.40 else "GREEN",
        "total_words": total_words,
        "ttr_sample_size": min(len(all_words), 500),
        "ttr_unique": len(set(first_500)),
        "ttr": ttr,
        "ttr_rating": "RED" if ttr > 0.72 else "YELLOW" if ttr > 0.65 else "GREEN",
        "hedge_count": hedge_count,
        "hedge_density": hedge_density,
        "hedge_rating": "RED" if hedge_density > 8 else "YELLOW" if hedge_density > 5 else "GREEN",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: compute_metrics.py <draft_file>"}))
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    print(json.dumps(compute_metrics(text), indent=2))
