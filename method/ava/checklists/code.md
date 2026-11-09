# Checklist: Code Activity
Use this checklist for every activity with TYPE: CODE (activity-list Phase 7 onward).
Design activities keep checklists/artifact.md, including its "no code" rule.

## Pre-generation
- [ ] method/laws.md has been read (laws and platform rules R1-R14)
- [ ] Activity ID, name, description, dependencies and threshold are understood
- [ ] The design artifact the code implements is APPROVED and is the input
- [ ] LAW 3 search recorded: existing tools checked before writing any code
- [ ] Prompt saved to audit/prompts/[task_id]_prompt.md

## Gate 1 (deterministic, before the Senior review)
- [ ] Tests written for the change and passing
- [ ] Linters and static checks passing; no new warnings in changed files
- [ ] Secret scan clean
- [ ] Every new or changed CI action or step pinned to a commit SHA (or the CI system's equivalent)
- [ ] Every new dependency pinned (version and hash) and its licence on the allowed list
      (until the licence verifier exists in 7.9: the SPDX licence file is read and recorded in the AvA log)
- [ ] No client data, project code or secrets in the public repository
- [ ] Files changed only inside the activity's output path (allowed paths)
- [ ] Every novel failure met during the work added as a regression fixture (rule R8)

## Senior review (Gate 2)
- [ ] Senior route on a different vendor from the Junior (or OD-1 limitation recorded in the log)
- [ ] Score meets the threshold (never below 88); canary result recorded when scheduled
- [ ] The change matches the design artifact; deviations listed and justified

## Output compliance
- [ ] AvA log saved to audit/ava_logs/[task_id]_round[n].md (audit/ after activity 7.2)
- [ ] One squashed commit per push, standard PR title
- [ ] Decision file left PENDING for the human
