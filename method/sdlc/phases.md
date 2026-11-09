# VASH 3.0 — SDLC Phases Complete Sequence

Projects in iterative mode run only Phases 1-3 once, then the feature loop of sdlc/iteration-mode.md.

VASH 3.0 follows a structured SDLC with 8 phases. Each has defined entry/exit criteria,
responsible groups, artifacts produced, parallel execution opportunities, and a human gate.

## Phase 1: Brief Intake

**Purpose:** Transform the human's brief into a validated, structured input ready for
decomposition.

**Privacy (Amended by 2.6, rule R2):** The brief and any client data are processed by the local
model only; raw input is kept in the project's git-ignored intake folder.

**Entry criteria:** Human submits a project brief via a work item on the project's forge.

**Exit criteria:** Brief validated against Handshake 1 schema; all required fields present;
PM confirms understanding.

**Responsible group:** Group 1 (Discovery) — PM leads.

**Activities:** Read and parse brief; validate required fields; identify ambiguities; create
activity list; identify which groups are needed.

**Artifacts produced:** Validated brief, preliminary activity list.

**Parallel safe:** NO.

**Human gate:** YES — human confirms brief is correctly understood.

## Phase 2: Requirements Discovery

**Purpose:** Translate the validated brief into complete, verifiable functional requirements.

**Entry criteria:** Validated brief approved by human.

**Exit criteria:** All FRDs approved by human; every requirement has acceptance criteria;
scope boundaries confirmed.

**Responsible group:** Group 1 (Discovery) — BA leads, UX supports.

**Activities:** Stakeholder analysis; Functional requirements decomposition; User story mapping;
Acceptance criteria definition; Scope boundary confirmation; UX requirements definition.

**Artifacts produced:** FRDs, User story map, Acceptance criteria document, UX requirements spec,
Scope confirmation document.

**Parallel safe:** BA and UX work in parallel once brief is decomposed.

**Human gate:** YES — human approves all FRDs before architecture begins.

## Phase 3: Architecture Design

**Purpose:** Define the technology-agnostic system architecture and all major technical
decisions.

**Entry criteria:** Approved FRDs from Phase 2.

**Exit criteria:** All ADRs approved; data models approved; API contracts approved; technology
selections justified with LAW 1 compliance.

**Responsible group:** Group 2 (Architecture) — SA leads, DE supports.

**Activities:** High-level design (HLD); Technology selection (one ADR per major decision);
Data model design; API contract definition; Security design principles; Integration design;
LAW 1 compliance verification; Stack selection from catalog (Amended by 2.6); Catalog gap
handling (Amended by 2.6).

**Artifacts produced:** HLD document; ADRs per decision; Stack ADR (PROPOSED to ACCEPTED by
human) in the project repository (Amended by 2.6); On ACCEPTED: project-stack.json written by
the engine and the project repository provisioned, deterministic, no AI (Amended by 2.6);
Entity-relationship diagrams; API contracts; Security design; Integration map.

**Parallel safe:** Data model and API contracts run in parallel after HLD approval.

**Human gate:** YES — human approves HLD and ADRs before engineering begins.

## Phase 4: UX Design

**Purpose:** Define all user interaction patterns, flows, and component specifications.

**Entry criteria:** Approved FRDs from Phase 2.

**Exit criteria:** All user flows approved; component specs complete; accessibility requirements
defined.

**Responsible group:** Group 3 (UX) — UI/UX Designer leads.

**Activities:** User flow definition per user type; Component specification; Interaction pattern
library; Error state definitions; Accessibility requirements (WCAG compliance); Responsive
design.

**Artifacts produced:** User flow documents; Component specification library; Interaction
pattern document; Accessibility requirements; Error state catalog.

**Parallel safe:** YES — runs in parallel with Phase 3 Architecture.

**Human gate:** YES — human approves UX flows before engineering begins.

## Phase 5: Engineering Design

**Purpose:** Translate architecture decisions and UX specs into detailed technical
specifications.

**Entry criteria:** Approved HLD from Phase 3 + approved UX flows from Phase 4.

**Exit criteria:** All module designs approved; API implementation specs complete; service
boundaries defined.

**Responsible group:** Group 4 (Engineering) — SE leads, DE supports.

**Activities:** Module design and interface definitions; API implementation specifications;
Database schema finalisation; Service boundary definitions; Error handling specifications;
Performance requirements.

**Artifacts produced:** Module design documents; Detailed API specs; Final database schemas;
Service mesh design; Error catalog; Performance SLA document.

**Parallel safe:** Frontend and backend specs can run in parallel.

**Human gate:** YES — human approves engineering design before QA and infra begin.

## Phase 6: Quality Assurance Design

**Purpose:** Define comprehensive test strategies, test cases, and quality gates.

**Entry criteria:** Approved FRDs from Phase 2 + API contracts from Phase 3.

**Exit criteria:** All test plans approved; every requirement has a test case; every API
endpoint has edge case tests.

**Responsible group:** Group 5 (QA) — QA Engineer leads.

**Activities:** Test strategy definition; Unit test case authoring; Integration test case
authoring; Edge case cataloguing; Performance benchmark definition; Security test scenarios;
AI evaluation framework; Regression test planning.

**Artifacts produced:** Test strategy document; Test case catalogs; Edge case catalog;
Performance specifications; Security test plan; AI evaluation framework.

**Parallel safe:** YES — runs in parallel with Phase 5 Engineering Design.

**Human gate:** YES — human approves test plans before blueprint.

## Phase 7: Infrastructure Design

**Purpose:** Design the deployment architecture, CI/CD pipelines, and operational runbooks.

**Entry criteria:** Approved ADRs from Phase 3.

**Exit criteria:** All IaC designs approved; CI/CD pipeline designed; deployment runbooks
complete.

**Responsible group:** Group 6 (Infrastructure) — DevOps Engineer leads.

**Activities:** Infrastructure design (technology-agnostic IaC); CI/CD pipeline design;
Environment definitions (dev/staging/prod); Monitoring and alerting design; Disaster recovery
design; Security hardening design; Deployment runbook authoring.

**Artifacts produced:** Infrastructure design document; CI/CD pipeline design; Environment
configuration schemas; Monitoring and alerting design; DR plan; Security hardening checklist;
Deployment runbooks.

**Parallel safe:** YES — runs in parallel with Phases 5 and 6.

**Human gate:** YES — human approves infrastructure design before blueprint.

## Phase 8: Blueprint Assembly

**Purpose:** Consolidate all phase outputs into a single, coherent technical blueprint.

**Entry criteria:** All phases 1-7 approved; all artifacts passed AvA; all human gates cleared.

**Exit criteria:** Blueprint approved by human; all artifacts indexed; deliverable package
complete.

**Responsible group:** All groups contribute — SA leads consolidation.

**Activities:** Artifact index compilation; Consistency check across all artifacts;
Cross-reference validation (requirements to design to tests); Conflict resolution; Blueprint
document assembly; Deliverable package preparation; Known limitations documentation;
Recommended next steps authoring.

**Artifacts produced:** Master technical blueprint; Artifact index; Known limitations document;
Recommended next steps; Project deliverable package.

**Parallel safe:** NO.

**Human gate:** YES — final human approval of complete blueprint.

## Phase Sequence and Parallel Map

```
Phase 1: Brief Intake
    ↓
Phase 2: Requirements Discovery
    ↓
Phase 3: Architecture Design ──── Phase 4: UX Design   (parallel)
    ↓
Phase 5: Engineering Design ──── Phase 6: QA Design ──── Phase 7: Infrastructure   (parallel)
    ↓
Phase 8: Blueprint Assembly
    ↓
Human Final Approval
```

## Dependencies

- Phase 1 before Phases 2, 3, 4
- Phase 2 before Phases 3, 4, 6
- Phase 3 before Phases 5, 7
- Phase 4 before Phase 5
- Phases 5, 6, 7 in parallel
- All phases before Phase 8

## Artifact Traceability Matrix

Brief to Requirements (Phase 2)
Requirements to Architecture decisions (Phase 3)
Requirements to UX flows (Phase 4)
Architecture + UX to Engineering specs (Phase 5)
Requirements + Architecture to Test cases (Phase 6)
Architecture to Infrastructure design (Phase 7)
All artifacts to Blueprint (Phase 8)

This ensures no orphaned artifacts and no untested requirements.

## Human Gate Summary

| Phase | Gate Trigger | What the Human Reviews |
|-------|--------------|------------------------|
| 1 | Brief validated | Brief understanding correct? |
| 2 | FRDs complete | Requirements complete and correct? |
| 3 | Architecture complete | ADRs and technology selections correct? |
| 4 | UX complete | User flows correct? |
| 5 | Engineering design complete | Module designs correct? |
| 6 | QA design complete | Test coverage adequate? |
| 7 | Infrastructure design complete | Infrastructure design correct? |
| 8 | Blueprint assembled | Blueprint complete and ready? |

## Amendment by 2.6 — Freeze Change Rule and Execution Stages

**Freeze change rule:** A project's project-stack.json changes only through a new ADR that
supersedes the earlier one, accepted by the human, followed by Stage 0 and the full pipeline.
A deterministic check refuses any change to the freeze file that does not name an ACCEPTED ADR.
Upgrading the pinned VASH version follows the same rule.

**Execution stages:** The build, review, pipeline, fix-loop, release and post-release stages
that follow Phase 8 are mapped in method/sdlc/execution-stages.md. They are execution stages,
not SDLC phases; they are built by activity-list Phase 7 (Engine Build) and apply to projects,
each in its own repository.
