# Checklist: Feature Activity
Use this checklist for every activity with TYPE: FEATURE (iterative mode, method/sdlc/iteration-mode.md).
A feature artifact is the design of one work item; the code that implements it is a later CODE activity
with the same `feature:` line.

## Pre-generation
- [ ] method/laws.md has been read (laws and platform rules R1-R14)
- [ ] The work item (issue) is linked on the `feature:` line, and its text is the input
- [ ] The accepted stack ADR and the project's standing rules (CLAUDE.md) have been read
- [ ] LAW 3 search recorded: existing components, packages and catalog entries checked before designing new ones
- [ ] Prompt saved to audit/prompts/[task_id]_prompt.md

## Content
- [ ] Goal: one paragraph, in the user's terms, for this feature only
- [ ] Requirements: numbered, each with acceptance criteria that a test can prove
- [ ] Scope: what is in, and what is explicitly out of this feature
- [ ] Design: components touched (screens, packages, tables, workflow), each in the component that owns it
- [ ] Dependencies in both directions: what this feature uses, and what uses the parts it changes
- [ ] Data: new or changed objects listed; every change to an existing object is an upgrade step, never an edit of a base script
- [ ] Security: roles and privileges per screen and action; data visibility rules
- [ ] Test plan: one test per acceptance criterion (database and UI), plus the regression tests the change needs
- [ ] Documentation: which docs change in the same PR (requirements, technical, user guide)
- [ ] Architecture or stack change: none, or a new ADR is named and the feature waits for its acceptance

## Laws
- [ ] LAW 1: no paid tool or service added
- [ ] LAW 2: human steps limited to approval of this design and the final merge
- [ ] LAW 3: reuse recorded; nothing rebuilt that exists

## Output compliance
- [ ] No client data, project code from another repository, or secrets
- [ ] No software code in the feature artifact (code belongs to the CODE activity)
- [ ] AvA log saved to audit/ava_logs/[task_id]_round[n].md
