# VASH 3.0 — Agent Handshake Contracts

Handshakes are the defined data contracts between agents at every role-to-role transition.

## Handshake 1: Human Owner to Project Manager

**Trigger:** Human submits a project brief.

**Data passed:** `BRIEF`
- `project_name`: string (required, non-empty)
- `domain`: string (required, industry/sector)
- `problem_statement`: string (required, > 50 characters)
- `target_users`: string (required)
- `constraints`: string (optional, budget/timeline/tech)
- `out_of_scope`: string (optional)

**Validation:** If any required field is missing, PM returns the template to the human.

**Format:** Work item body on the project's forge, or plain text in the PM chat.

## Handshake 2: Prompt Engineer to Junior Creator

**Trigger:** PM identifies the activity to run.

**Data passed:** `LOCKED_PROMPT`
- `activity_id`: string (required)
- `activity_name`: string (required)
- `task_description`: string (required)
- `laws_reference`: string (required, e.g. method/laws.md)
- `checklist_reference`: string (required, e.g. method/ava/checklists/code.md)
- `dependency_artifacts`: list[string] (paths must exist)
- `output_path`: string (required, within allowed_write)
- `output_format`: string (required)
- `threshold`: integer (88-100)
- `do_not`: list[string] (common mistakes)

**Validation:** output_path within allowed_write; threshold 88-100; dependency paths exist.

**Format:** Saved to audit/prompts/[task_id]_prompt.md.

## Handshake 3: Junior Creator to Senior Validator

**Trigger:** Junior completes artifact generation.

**Data passed:** `ARTIFACT_REFERENCE`
- `task_id`: string (required)
- `artifact_path`: string (required, non-empty)
- `activity_id`: string (required)
- `round_number`: integer (required)
- `checklist_path`: string (required)
- `laws_path`: string (required)

**NOT passed:** Junior's reasoning, previous Senior objections, any Junior session context.

**Validation:** artifact_path exists and is non-empty. Senior reads fresh.

**Format:** Environment variables passed to the Senior session.

## Handshake 4: Senior Validator to AvA Orchestrator

**Trigger:** Senior completes the review.

**Data passed:** `AVA_RESULT`
- `task_id`: string (required)
- `round_number`: integer (required)
- `score`: integer 0-100 (required)
- `verdict`: enum (APPROVED | MODIFY | FAIL)
- `checklist_results`: dict[item: PASS/FAIL]
- `law_results`: dict[LAW1/LAW2/LAW3: PASS/FAIL]
- `objections`: list[{id, location, issue}] (non-empty if MODIFY/FAIL)
- `corrections`: list[{objection_id, exact_fix}]

**Validation:** score 0-100; if MODIFY/FAIL, objections non-empty; each objection has exact
location.

**Format:** Saved to audit/ava_logs/[task_id]_round[n].md.

## Handshake 5: AvA Orchestrator to Human Owner

**Trigger:** Artifact passes threshold OR escalation triggered.

**Data passed (PASS):** `HUMAN_SUMMARY`
- `task_id`, `activity_name`, `score`, `verdict` (APPROVED), `summary` (2 sentences),
  `artifact_path`, `decision_options` (list: APPROVED / REJECTED / MODIFY)

**Data passed (ESCALATION):** `ESCALATION_SUMMARY`
- `task_id`, `activity_name`, `outcome` (ESCALATED), `reason`, `rounds_completed`,
  `score_trend` (list), `last_objections`, `recommended_action`

**Validation:** Summary in plain English; decision options explicit.

**Format:** Work item on project forge + audit/validation/[task_id]_summary.md.

## Handshake 6: Group Lead to Next Group Lead

**Trigger:** All activities in a group reach PASS + Human APPROVED.

**Data passed:** `GROUP_HANDOFF`
- `group_id`: string (required)
- `group_name`: string (required)
- `completed_artifacts`: list[{activity_id, path, score}]
- `key_decisions`: list[string] (references ADR or artifact paths)
- `constraints_for_next_group`: list[string]
- `open_questions`: list[string] (may be empty)

**Validation:** all completed_artifacts have STATUS PASS in plan/activity_list.md;
key_decisions reference specific ADR or artifact paths.

**Format:** Saved to audit/validation/[group_id]_handoff.md.

## Handshake 7: VASH to Human Owner (Project Complete)

**Trigger:** All groups complete and blueprint approved.

**Data passed:** `PROJECT_DELIVERABLE`
- `project_name`: string
- `total_artifacts`: integer
- `artifact_index`: list[{activity_id, name, path, score}]
- `blueprint_path`: string
- `total_ava_rounds`: integer
- `average_ava_score`: float
- `law_compliance`: dict[LAW1/LAW2/LAW3: percentage]
- `known_limitations`: list[string]
- `recommended_next_steps`: list[string]

**Format:** Saved to audit/validation/project_deliverable.md.
