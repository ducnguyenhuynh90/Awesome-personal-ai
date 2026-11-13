---
name: sop-writer
description: Writes or improves an SOP with owner, trigger, steps and checks. Use when a process must be documented, standardised or turned into a checklist / SOP.
metadata:
  department: operations
  tags:
  - sop
  - process
  - procedure
  - checklist
  - workflow
  - how we do
  - playbook
  - runbook
  examples:
  - Write an SOP for weekly payment reconciliation
  - Turn this Slack thread into a process for onboarding vendors
  writes_to:
  - outbox/
---

# sop-writer

Writes or improves an SOP with owner, trigger, steps and checks.

## Steps

1. Name: trigger, owner, inputs, output, frequency.
2. Steps: numbered, one action each, with the tool used and the done-check.
3. Exceptions and escalation path.
4. Save to outbox/ for the owner to publish (Notion is the source of truth for company SOPs).

## Output

Trigger · Owner · Steps (numbered) · Checks · Exceptions/escalation. Saved to outbox/.

## Quality checks

- Each step has one action and a done-check.
- Owner named.

## Pitfalls (learned)

- Writing what people should do instead of what they actually do — interview or read the thread first.
