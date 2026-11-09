# VASH 3.0 — AvA Protocol Rulebook

## What Is AvA

Agent vs Agent (AvA) is the adversarial quality control mechanism built into every VASH activity.
Every artifact is produced by a Junior agent and challenged by a Senior agent before any human
sees it. The two agents run in isolated context windows — the Senior has no memory of how the
Junior produced the artifact.

## Flow

1. The Junior receives the locked prompt and generates the artifact.
2. Gate 1 runs. On FAIL, the artifact returns to the Junior, unscored.
3. The Senior receives the artifact and the checklist only.
4. The Senior scores 0-100 and lists objections with locations.
5. Score >= threshold → APPROVED.
6. Score < threshold and round < 3 → the Junior addresses the objections, and the round repeats.
7. Round 3 without the threshold → stalemate table → ESCALATE or FAIL. Never APPROVED below
   the threshold.

## Gate 1 (deterministic)

Format checks (UTF-8, LF, no BOM, no trailing spaces, final newline), JSON/TOML/YAML/Python
syntax, schema validation, secret patterns, forbidden vendor names in vendor-free folders,
CI SHA pinning, placeholder detection. A Gate 1 failure stops the round before the Senior runs.

## Verdict Table

| Score | Verdict | Action |
|---|---|---|
| >= threshold | APPROVED | Promote artifact to audit/artifacts/, proceed |
| below threshold, rounds 1-2 | MODIFY | Return to Junior with objections |
| at round 3 | per stalemate table | ESCALATE (70 to below) or FAIL (< 70) |

## Stalemate Detection

Triggered when score improvement < 3 points over 2 consecutive rounds.

| Score at round 3 | Stalemate? | Action |
|---|---|---|
| >= threshold | any | APPROVED |
| 70 to below-threshold | yes | ESCALATE to human with score trend |
| 70 to below-threshold | no | ESCALATE (max rounds) |
| < 70 | any | FAIL — rebuild from scratch |

The Senior never auto-approves. Stalemate is always escalated to the human.

## Floor Rule (R5)

No artifact or change is approved below its threshold; no threshold is below 88.
A project may raise a threshold, never lower it.

## Max Rounds Rule

Maximum 3 rounds per activity per AvA session. If 3 rounds complete without reaching threshold:
apply the stalemate rule; if it does not resolve, FAIL; the human decides REJECTED or MODIFY.

## Canary Checks (R11)

The canary injector plants a known defect in a copy of the artifact under review. The interval
is set in the pool configuration (VASH's own dev) or in project-stack.json `canary.interval`
(projects). The Senior must report it as an objection. A missed canary invalidates that round's
score. Two consecutive misses escalate the Senior route to the human for change.

## Decision Commands (Human Gateway)

After the AvA loop, the human receives a plain-English summary with these commands:
- `APPROVED [task_id]`: proceed to the next activity.
- `REJECTED [task_id] [reason]`: stop; the Junior restarts with the reason.
- `MODIFY [task_id] [correction]`: the Junior applies the corrections and resubmits.

## Owner Exception OD-1

For VASH's own development, the Junior and Senior may run on the same vendor (Claude).
Independence is then enforced by isolated contexts and, preferably, different models. The
limitation is recorded in each AvA log. Projects have no such exception (rule R4).

## AvA Log Format

Every round logs at audit/ava_logs/[task_id]_round[n].md with these fields:
- Score (0-100), threshold, verdict
- Checklist results (item: PASS/FAIL)
- Law results (LAW1/LAW2/LAW3: PASS/FAIL with reason)
- Gate 1 result (PASS/FAIL with checks run)
- Junior route and Senior route (vendor / model)
- Canary result (NONE / CAUGHT / MISSED)
- Objections (list with exact locations)
- Corrections (exact fix per objection)
