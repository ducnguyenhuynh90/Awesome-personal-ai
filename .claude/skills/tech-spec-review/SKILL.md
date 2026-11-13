---
name: tech-spec-review
description: Reviews a tech spec for correctness, risk, security, cost and operability. Use when a technical design, architecture or spec needs review for risks, gaps and alternatives.
metadata:
  department: engineering
  tags:
  - tech spec
  - architecture
  - design review
  - system design
  - api
  - scalability
  - technical
  examples:
  - Review this design doc for the new payments service
  - Is this architecture OK for 10x traffic?
---

# tech-spec-review

Reviews a tech spec for correctness, risk, security, cost and operability.

## Steps

1. Restate the goal and constraints in 2 lines.
2. Check: correctness, failure modes, security (secrets, auth, PII), data migration, observability, cost.
3. Top 3 risks with severity and a concrete fix each.
4. Questions the author must answer before build.

## Output

Line 1: approve / approve with changes / rework. Risks (≤3, severity, fix). Questions (≤5).

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Security and failure modes covered.

## Pitfalls (learned)

- Style nitpicks instead of risks.
