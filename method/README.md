# VASH Method

The VASH method is how every activity in this repository is done and judged.

## Files

**Laws and rules**
- `laws.md` — three laws and platform rules R1-R15; single source of truth.

**Agent vs Agent protocol**
- `ava/protocol.md` — flow, Gate 1, scoring, verdict and stalemate tables, floor, canary, OD-1, log format.
- `ava/thresholds.json` — per-artifact-type thresholds; floor 88.
- `ava/checklists/artifact.md` — design activities; no-code rule.
- `ava/checklists/code.md` — code activities; Gate 1, tests, SHA pins, licence, allowed paths.
- `ava/checklists/feature.md` — feature design activities (iteration mode).
- `ava/checklists/manual_step.md` — human-only steps.
- `ava/checklists/prompt.md` — locked prompts, before any Junior session.
- `ava/checklists/ava.md` — the AvA round itself: was it run correctly.

**Roles, groups, handshakes**
- `roles/registry.md` — ten roles, thresholds, Junior and Senior agent mapping, model assignment.
- `groups/groups.md` — seven groups: lead, support, phases, AvA pairings, sequencing.
- `handshakes/handshakes.md` — seven handovers with typed fields and validation rules.

**Lifecycle**
- `sdlc/phases.md` — design path: Phases 1-8, human gates, traceability, parallel map.
- `sdlc/execution-stages.md` — build path: Stages 0-10, actor, mode, gate per stage.
- `sdlc/freeze-lifecycle.md` — stack proposal, acceptance, freeze, catalog gap, changes, adoption.
- `sdlc/iteration-mode.md` — agile delivery: inception once, then one feature loop per work item.

**Forms**
- `templates/brief.md` — project brief.
- `templates/frd.md` — functional requirements document.
- `templates/adr.md` — architecture decision record.
- `templates/decision.md` — activity decision (APPROVED / REJECTED / MODIFY).
- `templates/activity.md` — activity entry (ID, TYPE, DEPENDS_ON, THRESHOLD).
- `templates/prompt.md` — locked prompt.
- `templates/ava-log.md` — AvA round log.
- `templates/skill.md` — new skill (Agent Skills standard, SKILL.md); used by `vash skill new`.
- `templates/agent.md` — new agent (VASH neutral format); used by `vash agent new`.

**Schemas**
- `schemas/project-stack.schema.json` — project-stack.json freeze file.
- `schemas/ai-manifest.schema.json` — catalog index.
- `schemas/stack-pack.schema.json` — stack pack manifest.

## Reading order

1. `laws.md`
2. `ava/protocol.md`
3. `ava/thresholds.json`
4. `roles/registry.md`
5. `groups/groups.md`
6. `handshakes/handshakes.md`
7. `sdlc/phases.md`
8. `sdlc/execution-stages.md`
9. `sdlc/freeze-lifecycle.md`
10. `sdlc/iteration-mode.md`
11. `templates/*` (skim)
12. `schemas/*` (consult)
