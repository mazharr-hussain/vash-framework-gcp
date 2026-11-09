# VASH 3.0 — Three Laws and Platform Rules

## The Three Laws (changed only by an ACCEPTED ADR)

LAW 1 VANILLA FIRST ($0):
Everything VASH builds and runs uses open source and free tiers only. No paid SaaS.
Use the free tiers of all well-known vendors (LLMs, CI/CD, cloud), pooled through vetted
open-source tools. OCI Always Free is the execution engine and privacy fallback.
Software built BY VASH: open source, database-agnostic, cloud-agnostic, no lock-in.
Owner exception (D10, owner decision OD-1, 5 Nov 2026): VASH's own development uses Claude as its
main AI tooling until the owner changes this by a new ADR; it is not tied to any activity. The $0 rule
applies in full to every project: no project depends on a paid service.

LAW 2 AGENT OVER HUMAN:
If an agent or a script can do it, a human must not.
The human only: provides the brief, accepts ADRs (PROPOSED -> ACCEPTED), approves milestones,
and approves the final merge of a release.

LAW 3 SKILLS OVER REINVENTION:
Search the VASH catalog (ai-manifest.json, the project's project-stack.json) first, then vendor
and vetted open-source indexes. Reuse over reinvent. Check the licence before forking.
Document every search: what was searched, found, reused, built new and why.

## Platform Rules (enforced by the engine)

R1 PLATFORM ISOLATION: An application never changes shared platform data directly; it calls the
   platform's routine. Deterministic linters block violations.
R2 DATA PRIVACY: Client data and intake are processed only by the local model. Never sent to
   external free-tier APIs. Client data never enters the public VASH repository.
R3 DETERMINISTIC FIRST: Tests, linters, schema and secret checks (Gate 1) run before any AI
   review. A Gate 1 failure returns to the Junior / Coder; the Senior / Critic is not invoked.
R4 INDEPENDENT CRITIC: The Senior / Critic runs on a different vendor from the Junior / Coder.
   Owner exception OD-1: while VASH's own development uses Claude, its Junior and Senior may run on
   the same vendor, in isolated contexts, preferably on different models, with canary checks (R11) once the canary injector exists (activity 7.9; until then none);
   recorded in each AvA log. Projects have no such exception.
R5 HARD FLOOR: No artifact or change is approved below its threshold; no threshold below 88.
R6 MCP-ONLY WRITES: Build agents write files only through the MCP write tool, inside the
   allowed paths of the Freeze file.
R7 PROJECT FREEZING: A project loads only what its project-stack.json lists. The Freeze file is
   written by the engine from an ACCEPTED ADR and never edited by hand.
R8 CLOSED LOOP: Every novel pipeline failure becomes a deterministic check with a regression
   fixture. Improvements found in a project return to VASH only as generic, cleaned rules.
R9 VENDOR-NATIVE STATE: Project state lives on the chosen git host, read and written through
   the forge adapter. No third-party sync tools.
R10 COST METER: Hosted minutes, storage and tokens are measured every run; warn at 70 %,
   switch private projects' jobs to the self-hosted runner at 90 %.
R11 CANARY: The Critic is periodically tested with a planted defect; a missed canary invalidates
   the round's score.
R12 REUSE POOLING TOOLS: LLM pooling and failover use a vetted open-source tool; no custom
   routing logic. One configured fallback route (local Ollama).
R13 HARDWARE REALITY: Local AI fits the OCI Always Free A1 allowance; one heavy job at a time.
R14 FIX-LOOP CAP: At most 3 automatic fix attempts, then escalation to the human.
R15 REPEATED WORK BECOMES A SKILL: Work done 3 or more times in the same way becomes a skill
   (`vash skill suggest` finds it in audit/prompts/). Skills use the open Agent Skills format
   (SKILL.md, agentskills.io) so that every model and coding tool can use them; agents use VASH's
   neutral agent format (method/templates/agent.md). Generic skills go to the catalog without client
   names; project-specific skills stay in the project's skills/ folder.

## PARALLEL RULE
Activities marked PARALLEL_SAFE: YES can run together.
Activities with dependencies must run sequentially.
The orchestrator manages parallel execution.
