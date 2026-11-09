# catalog/ai_models.md

## Purpose
Reference for AI model routing. Read during Phase 3 activity 3.3 and when writing a project's
project-stack.json. Every limit here changes often: verify in activity 3.3 before use.

## Routing Rules (from method/laws.md)
| Rule | Meaning |
|------|---------|
| R2 Data privacy | Intake and any client data: local model only |
| R4 Independent critic | Senior / Critic on a different vendor from Junior / Coder |
| R12 Pooling tools | Pooling and failover through a vetted open-source tool; no custom routing |
| LAW 1 | Free tiers only; local model as the final fallback |

## Pooling Tool Candidates (decided in 3.3 by ADR)
| Tool | Status | Notes |
|------|--------|-------|
| freellmpool | Named by Blueprint v8.2; found on PyPI (see update below) | Maintenance, data-use terms, local fallback route (local models are not auto-routed) |
| LiteLLM | Previous VASH reference (open source) | Fallback candidate if freellmpool fails verification |

Update 5 Nov 2026 (MODIFY 1 of 2.6): freellmpool on PyPI - latest 0.13.0 (30 Aug 2026), Beta, MIT, source
github.com/0xzr/freellmpool; OpenAI-compatible proxy / library / CLI / MCP server; 22 providers; failover and
daily usage. Imported local models (Ollama, LM Studio, llama.cpp) are excluded from automatic routing, so the
local fallback is a separate route. Maintenance and data-use terms still to verify in 3.3.

## Harness Bridge (owner request, 2.6 MODIFY 1)
| Tool | What it does | Licence / use | To verify in 3.3 |
|------|--------------|---------------|------------------|
| free-claude-code (github.com/Alishahryar1/free-claude-code) | Local proxy that runs coding-agent harnesses (Claude Code, Codex, OpenCode, Cline, Aider, others) on about 60 providers (NVIDIA NIM default, OpenRouter, Groq, Gemini, Cerebras, Cloudflare, Ollama, LM Studio, llama.cpp, custom OpenAI-style) | AGPL-3.0-only: run unmodified as a separate local service, never forked or linked into VASH; proxy authentication (off by default) required on, loopback only; open-source harness by default | Provider terms for automated use, data use per provider, harness terms for Claude Code on other backends, release cadence (frequent tagged releases; pin a tag), "1.3B+ free tokens" claim |

## Free-Tier Providers to Evaluate (named by Blueprint v8.2)
| Provider | Type | To verify in 3.3 |
|----------|------|------------------|
| Groq | Hosted inference, free tier | Limits, models, data-use terms |
| Cerebras | Hosted inference, free tier | Limits, models, data-use terms |
| Google Gemini | Hosted, free tier | Limits; whether free-tier prompts are used for training |
| OpenRouter | Router with free models; named pool provider and candidate critic route (2.6 Section 9.2a) | Daily limits of free models, data-use / logging terms per free model |
| GitHub Models | Hosted, free tier with GitHub account | Limits |
| Mistral | Hosted, free tier | Limits, data-use terms |
| Cohere | Hosted, trial / free tier | Limits, commercial-use terms |
| Cloudflare Workers AI | Hosted, free daily allowance | Limits |
| Ollama (local, on OCI A1) | Self-hosted, open source (MIT); the only route for client data; final fallback | Fits A1 memory with one 7B coder model (v8.2: qwen2.5-coder:7b); Ollama cloud models count as external |
| NVIDIA NIM | Hosted inference, free developer tier (FCC default provider) | Limits, data-use terms |

Data-use terms matter: a free tier that may use prompts for training is allowed only for
public, non-client content (VASH's own design work), never for client data (R2).

## Route Assignment
| Use | Route |
|-----|-------|
| Intake, client data | Local Ollama |
| Junior / Coder | Pool route A |
| Senior / Critic | Pool route B — different vendor from route A |
| Exhausted free tiers | Local Ollama |

## Owner Exception (OD-1, answered 5 Nov 2026)
VASH's own development uses Claude as its main AI tooling for Junior and Senior until the owner
changes it by a new ADR. Free routes (pool, OpenRouter, free-claude-code) stay optional for VASH's
own work (OD-7). Projects always use the free routes above.
This is recorded as a known limitation (same vendor) in each AvA log.
