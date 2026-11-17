---
name: prd-draft
description: 'Drafts a lean PRD: problem, users, scope, requirements, metrics, risks. Use when a feature or change needs a product requirements doc or spec for design and engineering.'
metadata:
  department: product
  tags:
  - prd
  - spec
  - requirements
  - feature
  - user story
  - scope
  - product doc
  examples:
  - Write a PRD for one-tap deposit with GCash
  - Spec the new referral flow
  writes_to:
  - outbox/
---

# prd-draft

Drafts a lean PRD: problem, users, scope, requirements, metrics, risks.

## Steps

1. Problem and evidence first; if missing, run idea-to-hypothesis.
2. Users and jobs-to-be-done; in scope / out of scope.
3. Requirements as numbered, testable statements; edge cases; market-specific rules.
4. Success metric + guardrails; tracking events needed.
5. Save to outbox/; ticket creation is done by the ticketing agents, not here.

## Output

PRD in outbox/<task>-prd.md: Problem · Users · Scope (in/out) · Requirements (numbered) · Metrics · Tracking · Risks · Open questions. Reply = line 1 summary + link.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Each requirement is testable.
- Out-of-scope list exists.

## Pitfalls (learned)

- Solution-first PRDs with no problem evidence.
