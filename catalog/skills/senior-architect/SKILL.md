---
name: senior-architect
description: Review architecture decisions and technology selections for VASH 3.0. Use during Phase 3 technology decisions, Phase 5 platform design, and any artifact involving infrastructure, platform, or technology choices. Adapted from alirezarezvani/claude-skills.
license: MIT
metadata:
  vash-type: skill
  vash-source: catalog/skills/senior-architect
  vash-use: fork
  vash-version: 1.0.0
  vash-commit: to-verify
  vash-status: candidate
  vash-upstream: github.com/alirezarezvani/claude-skills
---

# Senior Architect Skill

## Source
Adapted from: alirezarezvani/claude-skills (senior-architect)
Original: github.com/alirezarezvani/claude-skills
LAW 3: Reused existing skill — not built from scratch

## When To Use
- Phase 3: All technology decision activities (3.1-3.7)
- Phase 5: All platform design activities (5.1-5.6)
- Any artifact involving infrastructure or platform choices
- Cross-role AvA for architecture-heavy artifacts

## Architecture Review Checklist

### Scalability
- Does the design scale from 1 to 1000 locations?
- Are there single points of failure?
- Can components be replaced independently?

### VASH Law Compliance
- LAW 1: Is every platform open source with free tier?
- LAW 1: Is technology agnostic (no stack locked in)?
- LAW 2: Is automation maximised at every layer?
- LAW 3: Were existing solutions searched before designing?

### Risk Assessment
- Top 3 scalability risks identified?
- Top 3 vendor lock-in risks identified?
- Mitigation strategy for each risk?

### Technology Decisions
- Every technology choice has documented reasoning?
- Alternatives considered and documented?
- Free tier confirmed for every platform?
- Exit strategy documented for each vendor?

## Output Format
```
ARCHITECTURE REVIEW SCORE: [0-100]

SCALABILITY RISKS:
1. [risk] — [mitigation]
2. [risk] — [mitigation]
3. [risk] — [mitigation]

LAW COMPLIANCE:
LAW 1 VANILLA: PASS/FAIL — [reason]
LAW 2 AGENT: PASS/FAIL — [reason]
LAW 3 SKILLS: PASS/FAIL — [reason]

TECHNOLOGY DECISIONS:
[decision]: SOUND/QUESTIONABLE — [reason]

RECOMMENDATION: APPROVED / MODIFY / REJECT
```
