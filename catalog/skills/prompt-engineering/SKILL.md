---
name: prompt-engineering
description: Generate optimal prompts for VASH activities. Use when starting any new activity, when a prompt needs to be created or improved, or when an AvA round fails due to unclear instructions. Adapted from NeoLabHQ/context-engineering-kit.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/prompt-engineering
  vash-use: fork
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
  vash-upstream: github.com/NeoLabHQ/context-engineering-kit
---

# Prompt Engineer Skill

## Source
Adapted from: NeoLabHQ/context-engineering-kit
Original: github.com/NeoLabHQ/context-engineering-kit
LAW 3: Reused existing skill — not built from scratch

## When To Use
- Before every VASH activity (generate the activity prompt)
- When Junior AvA score is below threshold due to unclear instructions
- When activity description is ambiguous

## Prompt Generation Workflow

### Step 1: Read Context
Read the current activity from plan/activity_list.md.
Read method/laws.md.
Read the relevant checklist from method/ava/checklists/.

### Step 2: Apply Anthropic Best Practices
- Be specific about what to produce
- Include positive AND negative examples where helpful
- Specify output format explicitly
- State constraints clearly
- Embed all three VASH laws

### Step 3: Prompt Structure
Every VASH prompt must include:
```
ACTIVITY: [ID] — [Name]
TYPE: [ARTIFACT/MANUAL]
LAWS: [reference to method/laws.md]
TASK: [specific description of what to produce]
CONTEXT: [relevant prior artifacts to read]
OUTPUT FORMAT: [exact format required]
OUTPUT PATH: [where to save]
CHECKLIST: [which checklist to validate against]
THRESHOLD: [minimum AvA score]
DO NOT: [common mistakes to avoid]
```

### Step 4: Validate Prompt
Before locking the prompt:
- Is the task unambiguous? Yes/No
- Is the output format specified? Yes/No
- Are all three laws referenced? Yes/No
- Is the output path clear? Yes/No
If any answer is No — revise before locking.

### Step 5: Save
Save locked prompt to: audit/prompts/[task_id]_prompt.md
Report: PROMPT LOCKED | Path: [path] | Ready for Junior Creator
