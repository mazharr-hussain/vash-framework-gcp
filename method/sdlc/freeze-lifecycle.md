# VASH 3.0 — Freeze Lifecycle

How a project's stack is proposed, accepted, frozen, provisioned, and later changed.

## Who Decides

| Step | Actor | Output | Gate |
|------|-------|--------|------|
| 1 Brief intake | PM (Group 1) | Validated brief | Human confirms brief |
| 2 Requirements | BA, UX (Group 1) | FRDs | Human approves FRDs |
| 3 Stack proposal | SA (Group 2) | Stack selection from the catalog | AvA threshold 90 |
| 4 ADR | SA | decisions/ADR-NNN-stack.md, status PROPOSED | - |
| 5 Human gate | Human owner | ADR status changed to ACCEPTED | Pipeline resumes only on ACCEPTED |
| 6 Freeze | Engine (deterministic) | project-stack.json written | Schema validation |
| 7 Provision | Engine (deterministic) | Submodules pinned, workflows pinned, audit folders | Stage 0 passes |
| 8 Use | Loader | Only the frozen agents and skills loaded | Stage 0 every run |

## Catalog Gap Handling

When the stack proposal needs an asset that the catalog does not yet hold:

| Step | Actor | Action |
|------|-------|--------|
| 1 | SA | Records the gap in the stack ADR |
| 2 | Prompt Engineer | Searches vendor indexes and vetted open-source indexes; records the search (LAW 3) |
| 3 | Engine (licence verifier) | Checks the licence of each candidate |
| 4 | AvA (threshold 90) | Reviews the asset as a technology selection |
| 5 | SA | Writes a catalog ADR in VASH |
| 6 | Human owner | ACCEPTS the catalog ADR |
| 7 | Engine | Forks the asset into catalog/external/ (submodule) or adds it as a VASH skill |
| 8 | Engine | Updates ai-manifest.json with the new entry |
| 9 | Project | Only then can the project freeze the asset |

## Fork vs Run

Assets VASH may fork or link are recorded in catalog/external/ as pinned git submodules.
Run-only tools (for example AGPL-3.0-only services) are recorded in ai-manifest.json with
use: run and installed at their pinned tag; they are never added as submodules.

## Changing a Frozen Stack

1. Change request as a work item on the project's forge.
2. New ADR that supersedes the earlier one (for example ADR-005 supersedes ADR-003).
3. AvA review, human ACCEPTED.
4. The engine rewrites project-stack.json.
5. Stage 0 and the full pipeline run.
6. A deterministic check refuses any change to project-stack.json that does not name an
   ACCEPTED ADR.

## Upgrading the VASH Version

The vash.version pin is part of the freeze. An upgrade follows the same process:
new ADR citing the release notes, human ACCEPTED, engine updates the pin, full pipeline runs.

## Adopting an Existing Project

A project whose stack was chosen before VASH (one of the owner's private projects) is adopted,
not redesigned:
1. The project's first ADR, "Adopt existing stack" (ADR ids are per repository; cross-repository
   references carry a repository qualifier), written by the SA from the project's current state,
   Status PROPOSED.
2. Human ACCEPTED.
3. The engine writes the project's project-stack.json from the current state.
4. The existing pipeline remains until the stack pack covers it.
5. Stack-specific pipeline parts move into the stack pack over time; the project then calls the
   pack instead of keeping its own copy.
