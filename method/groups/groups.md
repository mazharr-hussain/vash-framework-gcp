# VASH 3.0 — Group Configurations

Groups are collections of agent roles that collaborate on specific phases of a project.

## Group 1: Discovery and Requirements

**Purpose:** Transform a client brief into structured, verifiable requirements.

**Lead:** Business Analyst (BA)

**Support:** Project Manager, UI/UX Designer

**Phases covered:** Brief intake, Stakeholder analysis, Functional requirements, User stories,
Acceptance criteria.

**AvA pairings:** BA Junior to BA Senior (primary); UI/UX Junior to UI/UX Senior; cross-review:
BA Senior reviews UI/UX artifacts for requirement consistency.

**Entry criteria:** Approved project brief from human owner.

**Exit criteria:** All FRDs approved + acceptance criteria defined.

## Group 2: Architecture and Design

**Purpose:** Define the technology-agnostic architecture and all major technical decisions.

**Lead:** Solution Architect (SA)

**Support:** Data Engineer (DE), AI/ML Engineer (when AI components present).

**Phases covered:** System architecture, Technology selection (ADRs), Data model, API contract,
Security design, Integration design.

**AvA pairings:** SA Junior to SA Senior (primary, uses senior-architect skill); DE Junior to
DE Senior; cross-review: DE Senior reviews SA data architecture; SA Senior reviews DE pipeline
designs.

**Entry criteria:** Approved FRDs from Group 1.

**Exit criteria:** All ADRs approved + data models approved + API contracts approved.

## Group 3: User Experience

**Purpose:** Define all user interaction patterns, flows, component specifications.

**Lead:** UI/UX Designer

**Support:** Business Analyst (reference).

**Phases covered:** User flows, Component specs, Accessibility, Interaction patterns, Error states.

**AvA pairings:** UI/UX Junior to UI/UX Senior (primary); cross-review: BA Senior reviews UX
flows against requirements.

**Entry criteria:** Approved FRDs from Group 1.

**Exit criteria:** All user flows approved + component specs approved.

## Group 4: Engineering Design

**Purpose:** Translate architecture decisions into detailed technical specifications.

**Lead:** Software Engineer (SE)

**Support:** Data Engineer (DE), DevOps Engineer.

**Phases covered:** Module design, API implementation specs, Database schema finalisation,
Service boundaries, Error handling, Performance requirements.

**AvA pairings:** SE Junior to SE Senior (primary); DE Junior to DE Senior; cross-review: SE
Senior reviews DE schema for ORM compatibility; DE Senior reviews SE APIs for data access
patterns.

**Entry criteria:** Approved ADRs and data models from Group 2.

**Exit criteria:** All module designs approved + API specs approved.

## Group 5: Quality Assurance

**Purpose:** Define comprehensive test strategies, test cases, quality gates.

**Lead:** QA Engineer

**Support:** AI/ML Engineer (for AI component testing).

**Phases covered:** Test strategy, Unit tests, Integration tests, Edge cases, Performance
benchmarks, Security tests, AI evaluation.

**AvA pairings:** QA Junior to QA Senior (primary); cross-review: SE Senior reviews test cases
for technical feasibility; AI/ML Senior reviews AI evaluation frameworks.

**Entry criteria:** Approved FRDs + API contracts.

**Exit criteria:** All test plans approved + edge cases catalogued.

## Group 6: Infrastructure and Operations

**Purpose:** Design deployment architecture, CI/CD pipelines, operational runbooks.

**Lead:** DevOps Engineer

**Support:** Solution Architect (reference).

**Phases covered:** Infrastructure design (IaC), CI/CD pipeline, Environment definitions,
Monitoring, Disaster recovery, Deployment runbooks.

**AvA pairings:** DevOps Junior to DevOps Senior (primary, uses senior-architect skill);
cross-review: SA Senior reviews infrastructure for architecture compliance.

**Entry criteria:** Approved ADRs from Group 2.

**Exit criteria:** All IaC designs approved + deployment runbooks approved.

## Group 7: AI and Intelligence

**Purpose:** Design all AI/ML components, model selection, prompt strategies, evaluation
frameworks.

**Lead:** AI/ML Engineer

**Support:** Data Engineer, QA Engineer.

**Phases covered:** Model selection (ADRs), Prompt templates, RAG architecture, Fine-tuning
strategy, AI evaluation, Bias/safety.

**AvA pairings:** AI/ML Junior to AI/ML Senior (primary); cross-review: DE Senior reviews data
pipelines feeding AI components; QA Senior reviews evaluation frameworks.

**Entry criteria:** Approved FRDs + data models.

**Exit criteria:** All model ADRs approved + evaluation frameworks approved.

## Sequencing Rules

Group 1 must complete before Groups 2, 3, and 7.
Groups 2 and 3 can run in parallel after Group 1.
Group 2 must complete before Groups 4 and 6.
Groups 4, 5, 6, and 7 can run in parallel.
All groups must complete before Phase 8 (Blueprint Assembly).
