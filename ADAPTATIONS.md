# ADAPTATIONS

Tracks how CCMW (Claude Code My Workflow) skills and patterns have been adapted for CCVW (Claude Code Vaidehi Workflow). Each entry describes what changed and why.

---

## Writing analysis skills

| Skill | CCMW original | CCVW adaptation | Reason |
|-------|---------------|-----------------|--------|
| proofread | Single-agent lecture-file proofreader (grammar, typos, overflow, consistency, academic register) | 12-step multi-agent pipeline: 3 paired primary agents (surface, consistency, register), two-tier canonical vocabulary check (paired Canonical-1 + paired Canonical-2 self-discovery), dual challenger pair, single presentation agent. Essay-type-routed register brief (research vs personal/application/other). | Essay writing context requires domain-aware register checking and canonical terminology management across research projects. Single agent insufficient for confidence-tagged parallel analysis. |
| plagiarism-check | n/a (new skill) | 12-step pipeline: Tier 1 dual self-discovery (Glob filter on `type:: source` + project filter) → optional cache → post-Tier-1 scope gate → Tier 2 paired per-source agents + dual structural pair + dual voice pair → cross-structural/voice merge → dual challenger → presentation. Three modes: citation-check / full-scan / voice-only. | Domain: Bollywood costume studies — foundational sources (Dwyer, Ganti, Bhabha, Said) heavily engaged; structural mirroring expected in analytical writing. Challenger adjudicates context-appropriateness of structural and voice findings against essay type and disciplinary norms. |
| ai-detection-check | n/a (new skill) | 11-step pipeline: deterministic compute_metrics.py (CV, TTR, hedge density) + find_ai_patterns.py (14 patterns) prescans → dual quant + dual pattern + dual voice/texture agents → calibration gate → cross-B/C merge → dual challenger → presentation. Strict-scope challenger (does not infer norms from training data for adjacent fields). | Academic writing in film/fashion studies has specific hedging norms and vocabulary registers (Indian fashion terminology, transliterated terms). Generic AI detection thresholds need calibration to disciplinary standards. The strict-scope challenger prevents false positives on domain-standard analytical voice. |
| review-writing | n/a (new skill) | 10-step pipeline: 4 dual domain pairs (argument structure, clarity, evidence, voice) + dual challenger + presentation. Deterministic count_citations.py prescan for research essays. Essay-type-routed evidence and voice briefs. | Research essays and personal/application essays have distinct evidence standards (citation density vs concrete specificity). Argument and voice are different concerns for analytical vs application writing. Cross-domain merge for findings flagged by multiple domain pairs. |

## Convergence methodology

The four skills passed through an iterative trace + fix loop dispatched as Explore subagents. Each skill ran forward + backward traces (per `memory/context/context-{forward,backward}-trace-prompt.md`) on the SKILL.md and supporting files. Every issue surfaced was fixed inline; the next round verified. Convergence: when a round surfaces only edge-case completeness gaps that don't risk runtime data loss.

The first two skills (proofread + ai-detection-check) ran 8 rounds each — the slow convergence yielded 23 generalisable bug-WHYs that became the cross-skill lesson catalogue. The last two (review-writing + plagiarism-check) inherited the lessons via a converged template and converged in 2 and 5 rounds respectively, validating lesson #21 (template-driven builds converge dramatically faster than from-scratch).

## Trace prompt updates

`memory/context/context-forward-trace-prompt.md` and `context-backward-trace-prompt.md` track the canonical evaluator definitions used by all trace agent dispatches. Updates over the build:
- Forward trace: agent description string consistency check, variable placeholder namespace check, mode-conditional completeness check
- Backward trace: Pass 2 step-level input check (in addition to the original Pass 1 script-output check)
