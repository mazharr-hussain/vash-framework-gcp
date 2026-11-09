# Iteration Mode (agile delivery)

How a project delivers feature by feature instead of designing everything up front.
A project chooses it in its freeze: `"delivery": {"mode": "iterative", "iteration_days": 14}`.
Without a `delivery` block the mode is phased (sdlc/phases.md, then sdlc/execution-stages.md).

## The two parts

**1. Inception (once per project)**
- Phase 1 Brief Intake, Phase 2 for the core requirements, Phase 3 Architecture Design.
- Ends with the stack ADR ACCEPTED and the project's standing rules written (CLAUDE.md).
- Phases 4-8 are not run as whole-project phases; their content moves into each feature.

**2. Feature loop (once per work item)**

| Step | What happens | Activity type | Human |
|------|--------------|---------------|-------|
| 1 Pick | The issue is put in the current iteration on the board | - | Chooses the iteration's issues |
| 2 Design | Requirements, design, data, security and test plan of this feature only | FEATURE (checklists/feature.md) | Approves the design |
| 3 Build | Code and tests that implement the approved design | CODE (checklists/code.md) | - |
| 4 Review | Gate 1, Senior score (floor 88), fix loop capped at 3 (R14) | - | After 3 failed rounds |
| 5 Pipeline | Project CI: every job green | - | - |
| 6 Release | The PR closes the issue (`Fixes #n`) | - | Final merge |

Every FEATURE and CODE prompt carries `feature: <issue id>`, and may carry `iteration: <name>`;
the AvA runner refuses a FEATURE or CODE prompt without `feature:` in iterative mode and writes both
values into each AvA log, so every log traces to its work item and iteration.

## Iteration rhythm

- **Start:** the human picks the issues for the iteration (`iteration_days` long).
- **During:** each issue runs the feature loop; any number run in parallel when they touch different components.
- **End:** review of what was merged, and a short summary in `audit/metrics/` (done, open, rounds and scores).
  Novel failures met in the iteration are already regression checks (R8).

## What does not change

- The three laws, R1-R14, Gate 1, the Senior review, the floor and the canary.
- ADRs: only for stack or architecture changes. A feature that needs one waits for its acceptance.
- Human jobs (LAW 2): brief, ADR acceptance, milestone approval (here: each feature design and each iteration review), final merge.

## Not yet in the engine

- Reading the iteration from the board and creating the feature prompts from the chosen issues (`vash iteration`).
- The iteration summary in `audit/metrics/`.
Until then the prompts are written by hand (templates/prompt.md, with the `feature:` and `iteration:` lines).
