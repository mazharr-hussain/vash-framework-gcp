# Checklist: AvA Validation

Use this checklist when running the Agent vs Agent (AvA) review loop.

## Setup
- [ ] Junior artifact is saved at audit/artifacts/[task_id]_artifact.md
- [ ] Prompt is saved at audit/prompts/[task_id]_prompt.md
- [ ] Round number tracked (max 3 rounds)

## Senior review criteria
- [ ] Artifact fully addresses the activity description
- [ ] All three VASH laws are upheld
- [ ] No actual software code present (design only)
- [ ] Output is complete — not summarised
- [ ] Language is unambiguous and actionable

## Scoring
- [ ] Score assigned out of 100
- [ ] Score meets or exceeds activity threshold
- [ ] AvA log saved at audit/ava_logs/[task_id]_round[n].md

## Decision
- [ ] APPROVED — score meets threshold, proceed
- [ ] MODIFY — score below threshold, Junior revises (max round 3)
- [ ] FAIL — 3 rounds exhausted without passing threshold
