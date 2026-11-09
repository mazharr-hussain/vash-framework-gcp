---
name: vash-creator
description: Generate VASH artifacts as Junior Creator. Use when starting any VASH activity that requires producing a new artifact. Reads activity from plan/activity_list.md, applies three laws, produces full artifact, saves to audit/artifacts/. Built custom — no marketplace equivalent for VASH-specific artifact generation.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/vash-creator
  vash-use: run
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
---

# VASH Creator Skill (Junior Role)

## Source
BUILT NEW — no marketplace equivalent found.
Search log: .claude/skills/search_log.md
Reason: VASH-specific activity list, laws, and output format
require custom implementation.

## When To Use
- Starting any ARTIFACT type activity
- After prompt-engineering skill generates locked prompt
- As the Junior in every AvA loop

## Creation Workflow

### Step 1: Read Context (minimal — only what needed)
```
Read: plan/activity_list.md (current activity only)
Read: method/laws.md
Read: method/ava/checklists/artifact.md
Read: DEPENDS_ON artifacts from audit/artifacts/ if any
DO NOT: load entire repo into context
```

### Step 2: Validate Understanding
Before creating confirm:
- Activity ID and name understood
- Output path confirmed
- Threshold known
- All dependencies read

### Step 3: Create Artifact
Apply all three laws while creating:
- LAW 1: No proprietary platforms, free tier only
- LAW 2: Automation-first in every recommendation
- LAW 3: Document any search performed

Content rules:
- Full content — never summarise
- No actual software code — design and planning only
- Clear, structured, actionable language
- Address 100% of activity description

### Step 4: Self-Check Before Saving
- Does it fully address the activity? Yes/No
- Is it design only, no code? Yes/No
- Are all three laws applied? Yes/No
- Is it complete — no placeholders? Yes/No
If any No — revise before saving.

### Step 5: Save
Save to: audit/artifacts/[task_id]_artifact.md
Report:
```
ARTIFACT CREATED
Activity: [ID] — [Name]
Path: audit/artifacts/[task_id]_artifact.md
Self-check: PASS
Ready for: vash-validator skill
```
