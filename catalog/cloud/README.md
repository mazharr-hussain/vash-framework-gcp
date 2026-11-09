# catalog/cloud_free_tier.md

## Purpose
Reference for free-tier infrastructure. Read during activity 3.4 and activity-list Phase 7 (7.6, 7.10).
Every figure here changes over time: verify in activity 3.4 before use.

## LAW 1 Rule
$0: free tiers and open source only. A paid tier is never selected for the baseline.

## Execution Engine (Blueprint v8.2)
| Provider | Resource | Published Always Free allowance | Use in VASH |
|----------|----------|--------------------------------|-------------|
| Oracle Cloud | Ampere A1 (ARM64) compute | 4 OCPU / 24 GB in total (v8.2 sizes one VM at 2 OCPU / 12 GB) | Self-hosted runner for private projects' heavy jobs; local model (Ollama) |
| Oracle Cloud | Autonomous Database (Always Free) | Small fixed instances; session limit (v8.2: 30) | Database for Oracle stack projects; connections serialized |
| Oracle Cloud | Object Storage | Small free allowance | Terraform state, large test outputs (videos, traces) |
| Oracle Cloud | AMD micro VMs | 1 GB RAM each | Too small for the runner or the local model |
To verify in 3.4: idle-instance reclaim policy for Always Free compute, regional A1 capacity.

## GitHub (Free plan)
| Item | Public repository (VASH) | Private repository (projects) |
|------|--------------------------|-------------------------------|
| Hosted Linux minutes | Unlimited | 2,000 / month (Windows 2x, macOS 10x); each job rounded up to a whole minute |
| Branch protection / rulesets enforced | Yes | No |
| Environment required reviewers | Yes | No |
| Code scanning / secret push protection | Free | Not free |
| Artifact and package storage | Free | 500 MB |
| Actions cache | 10 GB per repository (to verify in 3.4) | 10 GB per repository (to verify in 3.4) |
| Self-hosted runners | Not used (untrusted code risk) | Used; a per-minute charge for self-hosted runners in private repositories may apply — verify in 3.4 |

## Overflow (emergency only, by ADR)
| Provider | Free CI allowance (to verify) |
|----------|-------------------------------|
| GitLab | Limited monthly compute minutes |
| Azure DevOps | One free parallel job with monthly minutes (grant may need a request) |

## Other Free Tiers (options for projects, chosen per project ADR)
| Category | Options |
|----------|---------|
| Compute | GitHub Actions, Google Cloud micro instance, Fly.io, Render (sleeps) |
| Database | Oracle Autonomous Database, Supabase PostgreSQL, Neon PostgreSQL, Turso SQLite, MongoDB Atlas |
| Storage | GitHub Releases, OCI Object Storage, Cloudflare R2, Backblaze B2 |
| Cache | Upstash Redis, Redis Cloud |
| CDN | Cloudflare |

## Baseline (replaces the earlier "Recommended Stack For VASH MVP")
| Layer | Choice | Why |
|-------|--------|-----|
| CI (VASH) | GitHub Actions hosted | Public: unlimited minutes |
| CI (projects) | GitHub Actions: light jobs hosted, heavy jobs on OCI A1 self-hosted | 2,000-minute limit |
| Local AI | Ollama on OCI A1 | Privacy (R2), fallback |
| State | GitHub Issues and Projects | Rule R9 |
| Artifacts | Git (audit trail), GitHub Releases, OCI Object Storage | Free |
| Infrastructure as code | Terraform | Open source |
