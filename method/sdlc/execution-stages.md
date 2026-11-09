# v8.2 Execution Stages

Execution stages are the build-and-run path a project follows after SDLC design is complete.
Every stage has a defined actor (Engine, AI, or Human), a mode (Deterministic or AI), and a gate.

## v8.2 Stage to VASH Phase Mapping

| Stage | VASH Phase or stage | Actor | Mode | Gate |
|-------|---------------------|-------|------|------|
| 0 | Before every phase | Engine | Deterministic | Halt on version mismatch |
| 1 | Phase 1 Brief Intake | PM, Group 1 | AI on local model only | Human confirms brief |
| 2 | Phase 1 exit / Phase 2 | PM | Deterministic | - |
| 3 | Phases 2-8 | BA, SA, UX, SE, DE | AI + AvA | ADR ACCEPTED by human |
| 4 | Execution stage (project) | SE, DE Coder | AI, MCP write tool only | - |
| 5 | Every artifact and change | Gate 1, Senior | Deterministic + AI | Floor 88 |
| 6 | Execution stage (project) | Engine | Deterministic | - |
| 7 | Execution stage (project) | Project CI | Deterministic | Every job green |
| 8 | Execution stage (project) | Coder | AI, hard cap 3 | Human after 3 |
| 9 | Execution stage (project) | Engine + human | Deterministic | Human approves merge |
| 10 | Execution stage (project) | Project CI | Deterministic | - |

## Stage Details

### Stage 0 — Ownership and dependency check

Compares vash.version in project-stack.json against the installed one. Halts on mismatch.
No AI is used.

### Stage 1 — Requirement intake

Raw human request to validated spec. Uses the local model only (rule R2).
External cloud APIs are never called with client data.

### Stage 2 — Work items

Creates work items on the project's forge (forge adapter chosen from the catalog).
Reads the project board. No AI is used.

### Stage 3 — Solution design and ADR gate

The Prompt Engineer group generates the DesignSpec. Critics review it.
The human sets the ADR status from PROPOSED to ACCEPTED. Pipeline halts until ACCEPTED.

### Stage 4 — Build

The Coder agent writes via the MCP write tool. Rule R6: writes only inside the allowed_write
globs of the freeze. Non-compliant paths raise WriteNotAllowed.

### Stage 5 — Offline review

Gate 1 (deterministic): format, syntax, secrets, vendors, SHA pins, placeholders.
If Gate 1 passes, the Senior (LLM) reviews for semantic quality. Floor 88.

### Stage 6 — Change request

One squashed commit per push. Standard PR title. No AI.

### Stage 7 — Pipeline execution

Light jobs on the project's hosted CI runners; heavy jobs on the project's self-hosted runner.
The cost meter tracks usage (rule R10). Alerts at 70%; switches at 90%.

### Stage 8 — Fix loop

The Coder reads the error log and proposes a fix. Capped at 3 attempts (rule R14). Then
escalates.

### Stage 9 — Release

Merge requires an ACCEPTED ADR + approval label. The human approves the final merge (LAW 2).
The engine tags the release and publishes it.

### Stage 10 — Post-release

The stack pack's browser test recipe runs against the live application.
Results are filed as work items on the project's forge.
