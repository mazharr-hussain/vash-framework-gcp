# VASH 3.0 — Global Laws

## Identity
You are working on VASH 3.0 — a Virtual AI Software House: the application framework
(method + engine + catalog) used by every application. Projects (KYC, COMMON, future
applications) live in their own private repositories and use VASH.
Until the blueprint (activity 6.1) is approved: design and plan only, no software code.
Engine code is in scope from Phase 7.
Follow the activity list in plan/activity_list.md in sequence.

## Three Laws — Never Broken (full text: method/laws.md)

LAW 1 VANILLA FIRST ($0):
Open source and free tiers only, from all well-known vendors, pooled by vetted open-source tools.
Software built by VASH: open source, agnostic, no lock-in.
Owner exception (OD-1): VASH's own development uses Claude as its main AI tooling until the owner
changes this by a new ADR. Every project stays $0.

LAW 2 AGENT OVER HUMAN:
Automate everything possible.
Human only: brief, ADR acceptance, milestone approval, final merge.

LAW 3 SKILLS OVER REINVENTION:
Search the catalog, then vendor and open-source indexes, before building.
Reuse over reinvent. Check licences.
Document what was searched and what was found.

## Platform Rules
R1-R15 in method/laws.md (isolation, privacy, deterministic first, independent critic,
hard floor, MCP-only writes, freezing, closed loop, vendor-native state, cost meter, canary,
pooling tools, hardware, fix-loop cap, repeated work becomes a skill).

## Public Repository
This repository will be public (activity 7.1). Write it as if it already were: never write client
data, project code, project AvA logs or secrets into it.

## AvA Rules
Junior generates. Senior reviews: a different vendor from the Junior for projects (R4); for VASH's
own work the same vendor is allowed under the owner exception (OD-1), in an isolated context.
Deterministic Gate 1 before every Senior review.
Max 3 rounds per activity.
Score must meet threshold before pushing; never approved below threshold.
All scores saved to audit/ava_logs/

## Output Rules
Every artifact: audit/artifacts/[task_id]_artifact.md
Every prompt: audit/prompts/[task_id]_prompt.md
Every AvA log: audit/ava_logs/[task_id]_round[n].md
Every validation: audit/validation/[task_id]_summary.md
Never skip saving. Never summarise. Full content always.
