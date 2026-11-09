# VASH 3.0 — Activity List

## Format
<!-- FORMAT BLOCK START
Each activity follows this structure:
ID: [phase.number]
NAME: [activity name]
TYPE: [ARTIFACT / MANUAL / CODE]  (CODE added by 2.6, checklist checklists/code.md)
PHASE: [phase name]
PARALLEL_SAFE: [YES / NO]
DEPENDS_ON: [activity IDs or NONE]
DESCRIPTION: [what to produce]
OUTPUT_PATH: [where to save]
CHECKLIST: [which checklist to use]
THRESHOLD: [minimum AvA score]
STATUS: PENDING

---

FORMAT BLOCK END -->

## Phase 0: Repository Setup

---
ID: 0.1
NAME: Create repository structure
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: NONE
DESCRIPTION: Create complete vash3-framework folder structure with README.md in each folder
OUTPUT_PATH: README.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

---
ID: 0.2
NAME: Fix corrupted files and create missing files
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.1
DESCRIPTION: Fix null byte corruptions in README files, remove PowerShell artifacts, create missing .github/CLAUDE.md and tech_providers files, complete activity list
OUTPUT_PATH: Multiple files
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.3
NAME: Create .claude/agents definitions
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: YES
DEPENDS_ON: 0.2
DESCRIPTION: Create subagent definition files for junior-creator, senior-validator, and prompt-engineer in .claude/agents/
OUTPUT_PATH: .claude/agents/
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

---
ID: 0.4
NAME: Create .claude/hooks definitions
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: YES
DEPENDS_ON: 0.2
DESCRIPTION: Create hook scripts for post-write logging, pre-delete protection of knowledge/, and session-end triggers
OUTPUT_PATH: .claude/hooks/
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.5
NAME: Search and install marketplace skills
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.2
DESCRIPTION: Search Claude Code marketplace for prompt-engineer, code-reviewer, senior-architect, multi-agent-patterns skills. Install confirmed matches. Document search results.
OUTPUT_PATH: .claude/skills/
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.6
NAME: Create custom VASH skills
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.5
DESCRIPTION: Create vash-creator, vash-validator, and vash-orchestrator SKILL.md files. Build only what marketplace did not have.
OUTPUT_PATH: .claude/skills/
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.7
NAME: Create GitHub Actions ava.yml
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: YES
DEPENDS_ON: 0.2
DESCRIPTION: Create GitHub Actions workflow that triggers on issue with label vash-activity. Runs Python ava.py script using Claude Code on GitHub VM.
OUTPUT_PATH: .github/workflows/ava.yml
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.8
NAME: Create GitHub Actions parallel.yml
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: YES
DEPENDS_ON: 0.2
DESCRIPTION: Create GitHub Actions workflow for running parallel PARALLEL_SAFE activities simultaneously using matrix strategy.
OUTPUT_PATH: .github/workflows/parallel.yml
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.9
NAME: Create GitHub Actions notify.yml
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: YES
DEPENDS_ON: 0.2
DESCRIPTION: Create GitHub Actions workflow that triggers on PR merge to main. Sends notification summary to human via Telegram or GitHub PR comment.
OUTPUT_PATH: .github/workflows/notify.yml
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 0.10
NAME: Create Python ava.py orchestrator
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.7
DESCRIPTION: Create Python script that orchestrates AvA loop. Calls Claude Code CLI for Junior and Senior sessions. Manages rounds, scores, and escalation. Reads from knowledge/, writes to runtime/.
OUTPUT_PATH: .github/scripts/ava.py
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

---
ID: 0.11
NAME: Create Python parallel.py orchestrator
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.8
DESCRIPTION: Create Python script that manages parallel activity execution. Identifies PARALLEL_SAFE activities, runs them concurrently, collects results.
OUTPUT_PATH: .github/scripts/parallel.py
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

---
ID: 0.12
NAME: Add ANTHROPIC_OAUTH_TOKEN to GitHub secrets
TYPE: MANUAL
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.7
DESCRIPTION: Generate Claude Code OAuth token via claude auth token command. Add as CLAUDE_CODE_OAUTH_TOKEN secret in GitHub repo settings. This enables Claude Code to run on GitHub VM using Claude.ai subscription.
OUTPUT_PATH: N/A
CHECKLIST: checklists/manual_step.md
THRESHOLD: 85
STATUS: PASS
---

---
ID: 0.13
NAME: End-to-end pipeline test
TYPE: ARTIFACT
PHASE: Phase 0 — Repository Setup
PARALLEL_SAFE: NO
DEPENDS_ON: 0.12
DESCRIPTION: Create test issue with label vash-activity. Verify full pipeline: issue created → GitHub Actions triggers → Claude Code runs AvA → result written to runtime/validation/ → PR created and merged.
OUTPUT_PATH: runtime/validation/0-13_summary.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PASS
---

---

## Phase 1: VASH Engine Vision

---
ID: 1.1
NAME: Define VASH 3.0 complete vision
TYPE: ARTIFACT
PHASE: Phase 1 — VASH Engine Vision
PARALLEL_SAFE: YES
DEPENDS_ON: 0.13
DESCRIPTION: Document what VASH is, what problem it solves, who it serves, what it produces, how it differs from existing solutions. This is the north star document.
OUTPUT_PATH: vash_framework/vision/1-1_vision.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 1.2
NAME: Define objectives and success metrics
TYPE: ARTIFACT
PHASE: Phase 1 — VASH Engine Vision
PARALLEL_SAFE: YES
DEPENDS_ON: 0.13
DESCRIPTION: Specific measurable objectives, success criteria per objective, how success is measured for each phase of VASH development.
OUTPUT_PATH: vash_framework/vision/1-2_objectives.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 1.3
NAME: Define scope and boundaries
TYPE: ARTIFACT
PHASE: Phase 1 — VASH Engine Vision
PARALLEL_SAFE: YES
DEPENDS_ON: 0.13
DESCRIPTION: What VASH does and does not do. In-scope vs out-of-scope features. Constraints and assumptions. What VASH 3.0 will NOT attempt to solve.
OUTPUT_PATH: vash_framework/vision/1-3_scope.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 1.4
NAME: Define stakeholder map
TYPE: ARTIFACT
PHASE: Phase 1 — VASH Engine Vision
PARALLEL_SAFE: YES
DEPENDS_ON: 0.13
DESCRIPTION: Who interacts with VASH, their roles, their needs, and their interaction points. Includes human owner, client, domain experts, and agent roles.
OUTPUT_PATH: vash_framework/vision/1-4_stakeholders.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 85
STATUS: PENDING
---

---

## Phase 2: Agent Architecture

---
ID: 2.1
NAME: Define 10 agent roles — complete registry
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 1.1, 1.2, 1.3, 1.4
DESCRIPTION: For each of the 10 roles: identity, persona, Jr/Sr definition, skills domain, AvA role, session types. Technology agnostic. No stack locked in.
OUTPUT_PATH: vash_framework/agents/2-1_agent_registry.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 2.2
NAME: Define AvA protocol rulebook
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 2.1
DESCRIPTION: Two AvA layers, scoring thresholds per artifact type, max 3 rounds, stalemate rules, escalation triggers, parallel AvA rules.
OUTPUT_PATH: vash_framework/agents/2-2_ava_protocol.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 2.3
NAME: Define 7 group configurations
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 2.1
DESCRIPTION: For each group: roles involved, AvA pairings, phases covered, cross-role review rules, parallel execution rules.
OUTPUT_PATH: vash_framework/agents/2-3_groups.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 2.4
NAME: Define handshake contracts
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 2.1, 2.3
DESCRIPTION: For each role-to-role handoff: data schema, required fields, validation rules. How artifacts are passed between agents and phases.
OUTPUT_PATH: vash_framework/agents/2-4_handshakes.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 2.5
NAME: Define SDLC phases — complete sequence
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 2.1, 2.2, 2.3, 2.4
DESCRIPTION: All 24 SDLC phases: name, purpose, entry criteria, exit criteria, roles involved, artifacts produced, parallel safety.
OUTPUT_PATH: vash_framework/agents/2-5_sdlc_phases.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 2.6
NAME: Re-baseline VASH as an application framework (Blueprint v8.2 merge)
TYPE: ARTIFACT
PHASE: Phase 2 — Agent Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 2.5
DESCRIPTION: Merge the owner's Master Architecture Blueprint v8.2 into VASH. Define VASH as the application framework (method + engine + catalog; core / stack pack / project layers), the stack decision and freeze lifecycle (VASH proposes, human accepts, VASH writes project-stack.json and provisions), v8.2 Stages 0-10 mapped to VASH phases, the project-stack.json and ai-manifest.json contracts, target repository structures, public VASH / private projects quota and gate model, LLM strategy, hardware limits, resolution of findings C1-C11, ADR-001, amendments to approved artifacts, provisional Phase 7.
OUTPUT_PATH: vash_framework/architecture/2-6_application_framework.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---

## Phase 3: Technology Decisions

---
ID: 3.1
NAME: Evaluate and decide AvA debate management platform
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: Review knowledge/tech_providers/platforms.md AvA options. Score each: free tier, open source, fits VASH. Select and justify. Free tier required. Amended by 2.6: include the supervisor graph candidate named by Blueprint v8.2 (LangGraph), interrupt-based ADR gate, hard floor, fix-loop cap; dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-1_ava_platform.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 3.2
NAME: Evaluate and decide human-in-loop platform
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: Review platform options for human approval channel. Select primary and fallback. Free tier confirmed. Document selection reasoning. Amended by 2.6: ADR file gate (PROPOSED -> ACCEPTED), merge gate per repository visibility and its residual risk (2.6 Section 8.3); dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-2_hitl_platform.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 3.3
NAME: Evaluate and decide AI model routing for client projects
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: Review knowledge/tech_providers/ai_models.md. Define routing rules for software BUILT BY VASH and (Amended by 2.6) optional free routes for VASH's own work (OD-1: Claude stays its main tooling until the owner changes it). Jr models, Sr models, cost per task estimate (under $0: free-tier quota and token use per task). Amended by 2.6: LAW 3 verification of the pooling tool named by v8.2 (freellmpool), Ollama (local), OpenRouter (free models), the free-claude-code harness bridge (AGPL run-only, provider terms for automated use; 2.6 MODIFY 1), a vetted local-fallback mechanism (R12: no custom failover logic), LiteLLM only as fallback candidate, different-vendor critic, local intake on Ollama, free-tier data-use terms, cost-meter token source; dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-3_model_routing.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 3.4
NAME: Evaluate and decide infrastructure platform
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: Review knowledge/tech_providers/cloud_free_tier.md. Select compute, storage, DB for VASH engine platform. Free tier only. Justify each choice. Amended by 2.6: OCI Always Free A1 and Autonomous Database, GitHub Free quotas public vs private, self-hosted runner charges, runner registration and host-wide lock, idle reclaim, A1 capacity; dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-4_infrastructure.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 3.5
NAME: Decide state and memory management
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: How VASH manages pipeline state, agent memory, session context. Free tier options. Open source preferred. Document selection. Amended by 2.6: GitHub Issues / Projects as vendor-native state, read-only status export, graph checkpoints; dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-5_state_management.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 3.6
NAME: Decide storage and artifact management
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: YES
DEPENDS_ON: 2.6
DESCRIPTION: Where VASH artifacts, logs, results are stored. GitHub as primary. Backup strategy. Free tier. Document selection. Amended by 2.6: audit/ committed vs runtime/ git-ignored, GitHub Releases and OCI Object Storage for large outputs, 500 MB private storage limit; dependency changed to 2.6.
OUTPUT_PATH: vash_framework/architecture/3-6_storage.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 3.7
NAME: Create Architecture Decision Record master
TYPE: ARTIFACT
PHASE: Phase 3 — Technology Decisions
PARALLEL_SAFE: NO
DEPENDS_ON: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
DESCRIPTION: Consolidate all technology decisions into one ADR. Every choice with reasoning, alternatives considered, free tier confirmation, open source confirmation.
OUTPUT_PATH: vash_framework/architecture/3-7_adr_master.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---

## Phase 4: Skills Architecture

---
ID: 4.1
NAME: Define skills taxonomy and governance
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: NO
DEPENDS_ON: 3.7
DESCRIPTION: Skill categories, naming conventions, versioning, single responsibility rule, no-AI-inside rule, reuse search requirement, skill dependency map. Amended by 2.6: include the VASH catalog (ai-manifest.json), stack-pack governance, allowed licences and the licence-verifier LAW 3 search.
OUTPUT_PATH: vash_framework/skills/4-1_skills_governance.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 4.2
NAME: Define orchestration skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All pipeline, routing, AvA, human gateway skills with signatures, inputs, outputs. Document search performed before building each skill.
OUTPUT_PATH: vash_framework/skills/4-2_orchestration_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.3
NAME: Define analysis skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All requirements, domain, risk, compliance skills with signatures, inputs, outputs.
OUTPUT_PATH: vash_framework/skills/4-3_analysis_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.4
NAME: Define architecture skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All HLD, ADR, data model, security design skills with signatures, inputs, outputs.
OUTPUT_PATH: vash_framework/skills/4-4_architecture_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.5
NAME: Define engineering skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All code generation, refactoring, integration, API skills with signatures, inputs, outputs.
OUTPUT_PATH: vash_framework/skills/4-5_engineering_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.6
NAME: Define quality skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All test generation, chaos, performance, E2E skills with signatures, inputs, outputs. Amended by 2.6: include the canary injector LAW 3 search (mutation-testing tools for code; design-artifact canaries).
OUTPUT_PATH: vash_framework/skills/4-6_quality_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.7
NAME: Define operations skills catalog
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: All IaC, CI/CD, monitoring, SRE, deployment skills with signatures, inputs, outputs.
OUTPUT_PATH: vash_framework/skills/4-7_operations_skills.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 4.8
NAME: Define domain pack template and governance
TYPE: ARTIFACT
PHASE: Phase 4 — Skills Architecture
PARALLEL_SAFE: YES
DEPENDS_ON: 4.1
DESCRIPTION: Domain pack schema, freshness rules, sensitivity levels, creation process, approval flow. Template for any industry. Amended by 2.6: cover stack packs (e.g. oracle-apex) alongside domain packs.
OUTPUT_PATH: vash_framework/skills/4-8_domain_pack.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---

## Phase 5: Platform Design

---
ID: 5.1
NAME: Design complete GitHub repository structure
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.7
DESCRIPTION: Final repo structure for VASH engine and all projects it will build. Folder hierarchy, naming conventions, file formats, branch strategy. Amended by 2.6: finalise 2-6_application_framework.md Section 7 (core and project repositories); complete the loader / provisioner LAW 3 search. Brought forward by owner decision (6 Nov 2026): records the structure frozen by the owner (D1-D9, ADR-002).
OUTPUT_PATH: vash_framework/platform/5-1_repo_structure.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 5.2
NAME: Design GitHub Actions automation architecture
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.7
DESCRIPTION: Complete design: all workflows, triggers, scripts, Claude Code OAuth, AvA loop automation, parallel execution, notification flow. Amended by 2.6: finalise Section 8 (runner split, gates, reusable workflows); complete the action / dependency pinning LAW 3 search.
OUTPUT_PATH: vash_framework/platform/5-2_gha_design.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 5.3
NAME: Design human gateway complete flow
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.2
DESCRIPTION: Telegram Bot or GitHub issues setup, message formats, decision routing, rate limiting, identity verification, APPROVED/REJECTED/MODIFY handling.
OUTPUT_PATH: vash_framework/platform/5-3_human_gateway.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 5.4
NAME: Design model router for client projects
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.3
DESCRIPTION: pooling tool or equivalent config for software built BY VASH. Routing rules, fallback chains, cost tracking, health monitoring. Amended by 2.6: route through the pooling tool chosen in 3.3 (no LiteLLM default), critic on a different vendor, local intake.
OUTPUT_PATH: vash_framework/platform/5-4_model_router.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 5.5
NAME: Design pipeline state management
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.5
DESCRIPTION: State schema, checkpoint format, recovery logic, session management. Free tier platform confirmed.
OUTPUT_PATH: vash_framework/platform/5-5_state_design.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 5.6
NAME: Design cost tracking and budget enforcement
TYPE: ARTIFACT
PHASE: Phase 5 — Platform Design
PARALLEL_SAFE: YES
DEPENDS_ON: 3.7
DESCRIPTION: How VASH tracks token costs per client project, enforces budget limits, alerts on overruns, reports usage. Amended by 2.6: the cost meter of 2.6 Section 8.4 (GitHub minutes and storage, tokens, A1 load; 70 % warn, 90 % switch). Amended by 2.6: complete the cost-meter LAW 3 search (GitHub billing usage API, pooling tool quota tracking).
OUTPUT_PATH: vash_framework/platform/5-6_cost_tracking.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---

## Phase 6: VASH Engine Blueprint

---
ID: 6.1
NAME: Produce complete VASH engine technical blueprint
TYPE: ARTIFACT
PHASE: Phase 6 — VASH Engine Blueprint
PARALLEL_SAFE: NO
DEPENDS_ON: 4.8, 5.6
DESCRIPTION: Master document combining all phase outputs into one coherent technical blueprint for building the actual VASH engine. Single source of truth.
OUTPUT_PATH: vash_framework/blueprint/6-1_blueprint.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 6.2
NAME: Produce VASH build roadmap
TYPE: ARTIFACT
PHASE: Phase 6 — VASH Engine Blueprint
PARALLEL_SAFE: NO
DEPENDS_ON: 6.1
DESCRIPTION: Sequenced plan for building the actual VASH engine. Phases, dependencies, milestones, estimated effort, parallel opportunities.
OUTPUT_PATH: vash_framework/blueprint/6-2_build_roadmap.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 6.3
NAME: Produce first project definition
TYPE: ARTIFACT
PHASE: Phase 6 — VASH Engine Blueprint
PARALLEL_SAFE: NO
DEPENDS_ON: 6.1
DESCRIPTION: Define the first real project VASH will build when operational. Scope, domain pack requirements, success criteria, estimated timeline.
OUTPUT_PATH: vash_framework/blueprint/6-3_first_project.md
CHECKLIST: checklists/artifact.md
THRESHOLD: 88
STATUS: PENDING
---

## Phase 7: Engine Build — activity-list phase (PROVISIONAL — added by 2.6, confirmed or changed by 6.2; not SDLC Phase 7)

---
ID: 7.1
NAME: Prepare VASH for public visibility
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 6.2
DESCRIPTION: Automated: full-history secret scan, MIT LICENSE, every action pinned to a commit SHA, safe workflow triggers, fine-grained token scopes checked. Human only: the visibility switch.
OUTPUT_PATH: runtime/validation/7-1_summary.md
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 7.2
NAME: Create the core repository structure
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.1
DESCRIPTION: Create the VASH core layout of 2.6 Section 7.1 as finalised by 5.1 (method/, framework/, stacks/, skills/, external/, iac/, tests/, audit/), move today's runtime/ audit folders to audit/ and update the workflows' paths, create the initial ai-manifest.json (schema_version, licences_allowed[]), without loss of history.
OUTPUT_PATH: repository root (the structure itself); record in audit/validation/7-2_summary.md
CHECKLIST: checklists/code.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 7.3
NAME: Freeze contract validator and Stage 0 check
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.2
DESCRIPTION: Build the project-stack.json and ai-manifest.json validators and the Stage 0 check (versions, catalog ids, licences, critic vendor, thresholds, canary settings, ACCEPTED ADRs) with regression fixtures.
OUTPUT_PATH: framework/tools/
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 7.4
NAME: Clean-slate loader and status export
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.3
DESCRIPTION: Build the loader (shell and PowerShell, copy fallback when symbolic links are unavailable) that loads only frozen agents and skills, links tracked hooks and settings, generates CLAUDE.md, and exports read-only project status through the GitHub CLI; reuse the tools chosen in 5.1.
OUTPUT_PATH: framework/loader/
CHECKLIST: checklists/code.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 7.5
NAME: Deterministic Gate 1 tools
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.3
DESCRIPTION: Build Gate 1: artifact format and no-code checks, schema checks, secret scan, linters, each with regression fixtures (rule R8).
OUTPUT_PATH: framework/tools/
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 7.6
NAME: A1 VM, self-hosted runner and local model
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.2
DESCRIPTION: Terraform modules and the Always Free environment for the A1 VM: self-hosted runner registration (per 3.4), host-wide lock for one heavy job at a time, Ollama with one coder model, pinned ARM64 tools with checksums.
OUTPUT_PATH: iac/
CHECKLIST: checklists/code.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 7.7
NAME: LLM pool, independent critic and local intake
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.3, 7.6
DESCRIPTION: Configure the pooling tool chosen in 3.3 (engine calls), the free-claude-code harness bridge if OD-7 is accepted (harness sessions), OpenRouter and other pool providers, the different-vendor critic route, local intake on the A1 model, the local fallback, and make the AvA scripts able to use two model routes (Junior and Senior on different vendors; required for projects, optional for VASH's own work under OD-1).
OUTPUT_PATH: framework/pool/
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 7.8
NAME: Supervisor graph with ADR gate and fix-loop cap
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.5, 7.7
DESCRIPTION: Build the supervisor flow (Supervisor, Prompt Engineer, Junior / Coder, Gate 1, Senior / Critic) with the ADR human gate, hard floor and MAX_RETRIES = 3; align the AvA scripts: no stalemate auto-approve, CODE activity type.
OUTPUT_PATH: framework/supervisor/
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---

---
ID: 7.9
NAME: Cost meter, canary injector, licence verifier
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.8
DESCRIPTION: Build or configure the three tools of 2.6 Sections 3.3, 8.4 and 9.4 from the tools chosen in the LAW 3 searches (2.6 Section 14.2), with their audit outputs.
OUTPUT_PATH: framework/tools/
CHECKLIST: checklists/code.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 7.10
NAME: Reusable workflows
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.9
DESCRIPTION: Reusable GitHub workflows for projects: light jobs hosted, heavy jobs self-hosted with the host-wide lock, merge gate and scheduled audit job of 2.6 Section 8.3, all actions pinned by SHA.
OUTPUT_PATH: .github/workflows/
CHECKLIST: checklists/code.md
THRESHOLD: 88
STATUS: PENDING
---

---
ID: 7.11
NAME: First stack pack (oracle-apex) and KYC adoption
TYPE: CODE
PHASE: Phase 7 — Engine Build (activity list)
PARALLEL_SAFE: NO
DEPENDS_ON: 7.10
DESCRIPTION: Build the oracle-apex stack pack from generic pipeline patterns (no client data) and adopt KYC through its own ADR 'Adopt existing stack' and project-stack.json in the KYC repository.
OUTPUT_PATH: stacks/oracle-apex/
CHECKLIST: checklists/code.md
THRESHOLD: 90
STATUS: PENDING
---
