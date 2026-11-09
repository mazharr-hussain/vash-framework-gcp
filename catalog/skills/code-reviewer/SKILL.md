---
name: code-reviewer
description: Review and score VASH artifacts as Senior Validator. Use when an artifact has been produced by Junior Creator and needs adversarial review. Checks completeness, law compliance, quality, and no-code rule. Adapted from alirezarezvani/claude-skills adversarial-reviewer.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/code-reviewer
  vash-use: fork
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
  vash-upstream: github.com/alirezarezvani/claude-skills
---

# Code Reviewer Skill (VASH Senior Validator)

## Source
Adapted from: alirezarezvani/claude-skills (adversarial-reviewer)
Original: github.com/alirezarezvani/claude-skills
LAW 3: Reused existing skill — not built from scratch

## When To Use
- After Junior Creator produces any artifact
- During every AvA round as the Senior reviewer
- When escalation review is needed

## Review Domains (9 checks)
Apply all 9 for every VASH artifact:

1. COMPLETENESS — Does it fully address the activity description?
2. LAW 1 VANILLA — Open source, free tier, no proprietary lock-in?
3. LAW 2 AGENT — Automation maximised, no unnecessary manual steps?
4. LAW 3 SKILLS — Search documented, reuse confirmed before building?
5. NO CODE RULE — Design and planning only, no implementation code?
6. STRUCTURE — Clear, logical, actionable sections?
7. SPECIFICITY — Concrete decisions, no vague statements?
8. CONSISTENCY — No contradictions with existing artifacts?
9. OUTPUT PATH — Saved to correct audit/ location?

## Scoring Rubric
- 90-100: Excellent — all 9 checks pass
- 80-89:  Good — 1-2 minor issues
- 70-79:  Acceptable — 3-4 issues, threshold dependent
- 60-69:  Poor — significant gaps, MODIFY required
- Below 60: Unacceptable — FAIL, rebuild required

## Output Format
Save to: audit/ava_logs/[task_id]_round[n].md

```
SCORE: [0-100]
THRESHOLD: [from activity]
VERDICT: APPROVED / MODIFY / FAIL

DOMAIN CHECKS:
1. Completeness: PASS/FAIL
2. LAW 1 Vanilla: PASS/FAIL
3. LAW 2 Agent: PASS/FAIL
4. LAW 3 Skills: PASS/FAIL
5. No Code Rule: PASS/FAIL
6. Structure: PASS/FAIL
7. Specificity: PASS/FAIL
8. Consistency: PASS/FAIL
9. Output Path: PASS/FAIL

OBJECTIONS (numbered, with exact location):
OBJ-001: [issue] at [exact location]

CORRECTIONS (exact fix per objection):
OBJ-001: [exact correction]
```
