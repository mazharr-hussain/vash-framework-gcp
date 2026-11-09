---
name: vash-validator
description: Review and score VASH artifacts as Senior Validator. Use after vash-creator produces an artifact. Runs adversarial review with no memory of how Junior produced the artifact. Scores 0-100 against VASH checklists. Built custom — no marketplace equivalent for VASH-specific scoring format.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/vash-validator
  vash-use: run
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
---

# VASH Validator Skill (Senior Role)

## Source
BUILT NEW — no marketplace equivalent found.
Search log: .claude/skills/search_log.md
Reason: VASH-specific checklists, scoring format, and
AvA output structure require custom implementation.
Uses code-reviewer skill internally for domain checks.

## When To Use
- After vash-creator produces any artifact
- As the Senior in every AvA loop
- When cross-role review is needed
- During escalation review in P2

## Validation Workflow

### Step 1: Read Context (minimal)
```
Read: plan/activity_list.md (current activity only)
Read: method/ava/checklists/artifact.md
Read: method/laws.md
Read: audit/artifacts/[task_id]_artifact.md
DO NOT: read Junior session history
DO NOT: load entire repo
```

### Step 2: Independent Review
Review as if seeing the artifact for the first time.
Apply code-reviewer skill for domain checks.
Apply senior-architect skill for architecture artifacts.

### Step 3: Score
Score 0-100 based on:
- Completeness (40%): fully addresses activity
- Law compliance (30%): all three laws respected
- Quality (20%): clear, structured, actionable
- No-code rule (10%): design only

### Step 4: Determine Verdict
```
Score ≥ threshold AND zero critical violations → APPROVED
Score within 10 of threshold → MODIFY
Score more than 10 below threshold → FAIL
Any LAW 1 violation → automatic FAIL
Any code found in artifact → automatic FAIL
```

### Step 5: Save and Report
Save to: audit/ava_logs/[task_id]_round[n].md

```
VASH VALIDATION RESULT
Activity: [ID] — [Name]
Round: [n]

CHECKLIST:
[each item]: PASS/FAIL

LAWS:
LAW1 VANILLA: PASS/FAIL — [one line]
LAW2 AGENT: PASS/FAIL — [one line]
LAW3 SKILLS: PASS/FAIL — [one line]

SCORE: [0-100]
THRESHOLD: [minimum]
VERDICT: APPROVED / MODIFY / FAIL

OBJECTIONS:
OBJ-001: [issue at exact location]

CORRECTIONS:
OBJ-001: [exact fix]
```
