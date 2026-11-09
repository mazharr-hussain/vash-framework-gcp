# catalog/platforms.md

## Purpose
Reference for platform selection. Read during Phase 3 technology decision activities.

## VASH Platform (fixed)
| Platform | Purpose | Cost | Why |
|----------|---------|------|-----|
| GitHub (VASH public, projects private) | Code, artifacts, automation, state (Issues, Projects) | Free plan | Version control, automation, vendor-native state (R9) |
| Python | Engine and scripts | Free | Open source |
| Pooled free-tier LLMs + local Ollama | All project AI work; optional for VASH's own work | Free | LAW 1, R2, R4, R12 |
| OpenRouter (free models) | One pool provider; candidate critic route | Free models | Many vendors behind one key |
| free-claude-code (run-only, AGPL) | Harness bridge: agent harness sessions on free providers (OD-7) | Free | Optional free route for VASH's own work; harness bridge for projects (OD-7) |
| OCI Always Free | Self-hosted runner, local model, database for Oracle-stack projects | Free | v8.2 execution engine |
| Claude tooling (owner exception, OD-1) | VASH's own development, until the owner changes it | Existing subscription | Owner decision 5 Nov 2026 (OD-1) |

## Platform Categories (options, decided by ADR)
### Orchestration and Pipeline
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| LangGraph | Open source | MIT | Self-host free (v8.2 candidate, decided in 3.1) |
| CrewAI | Open source | MIT | Self-host free |
| Temporal | Open source | MIT | Self-host free |

### Human-in-Loop Communication
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| GitHub Issues / PR / ADR file | SaaS | Proprietary | Free (v8.2 baseline: ADR PROPOSED -> ACCEPTED) |
| Telegram Bot | API | Free | Unlimited |
| Slack | SaaS | Proprietary | Limited free |

### State and Memory
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| GitHub Projects + read-only status export | SaaS | Proprietary | Free (R9 baseline) |
| SQLite (graph checkpoints) | Open source | Public domain | Always free |
| PostgreSQL | Open source | PostgreSQL licence | Self-host free |
| Redis (Upstash) | Managed | Open source | Limited free |

### Storage
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| GitHub (git, Releases) | SaaS | Proprietary | Free |
| OCI Object Storage | Managed | Proprietary | Always Free allowance |
| MinIO | Open source | AGPL | Self-host free |

## LAW 1 Compliance
All platforms must have an open-source alternative.
Free tier only. No proprietary lock-in in core logic.
Licences of every catalog asset are verified before use (licence verifier).
