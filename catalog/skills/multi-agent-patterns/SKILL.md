---
name: multi-agent-patterns
description: Orchestrate AvA loops between Junior Creator and Senior Validator agents. Use when managing multi-round AvA debates, when coordinating parallel activities, or when designing agent interaction patterns. Adapted from muratcankoylan/multi-agent-patterns.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/multi-agent-patterns
  vash-use: fork
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
  vash-upstream: github.com/muratcankoylan/multi-agent-patterns
---

# Multi-Agent Patterns Skill (VASH AvA Orchestrator)

## Source
Adapted from: muratcankoylan/multi-agent-patterns
Original: github.com/muratcankoylan/multi-agent-patterns
LAW 3: Reused existing skill — not built from scratch

## When To Use
- Managing any AvA loop between Junior and Senior
- Coordinating parallel PARALLEL_SAFE activities
- Designing agent handoff protocols
- Resolving AvA stalemates

## VASH AvA Orchestration Pattern

### Pattern: Junior → Senior Loop

```
ROUND 1:
1. Prompt Engineer generates locked prompt
2. Junior Creator receives prompt
3. Junior produces artifact
4. Save to runtime/drafts/[task_id]_draft.md
5. Senior Validator receives artifact
6. Senior reviews using code-reviewer skill
7. Senior saves score to audit/ava_logs/[task_id]_round1.md

EVALUATE:
- Score ≥ threshold → APPROVED → move to artifacts/
- Score < threshold AND rounds < 3 → MODIFY → back to Junior
- Rounds = 3 AND score < threshold → check stalemate rule

STALEMATE RULE:
- Score improvement < 3 points over 2 rounds = STALEMATE
- (Amended by 2.6, rule R5) never approved below threshold
- Score 70 to below threshold + stalemate → ESCALATE to human
- Score < 70 + stalemate → FAIL → rebuild
- Round 3, below threshold, no stalemate → ESCALATE to human
```

### Pattern: Parallel Execution

```
PARALLEL_SAFE activities can run simultaneously:
1. Identify all PENDING activities with PARALLEL_SAFE: YES
2. Check DEPENDS_ON — all dependencies must be PASS
3. Spawn separate AvA session per activity
4. Each session runs independently
5. Collect all results before human review
6. Present consolidated summary to human
```

### Pattern: Cross-Role Review

```
For critical artifacts use cross-role challenge:
1. Primary reviewer: same role Senior
2. Secondary reviewer: different role Senior
   - Architecture artifacts → senior-architect skill
   - Technology decisions → senior-architect skill
   - All artifacts → code-reviewer skill
3. Lower of two scores determines final verdict
```

## Handoff Protocol
Junior → Senior: pass artifact path only, not content
Senior → Human: pass summary only, not full artifact
Human → Junior: pass decision + specific corrections only
