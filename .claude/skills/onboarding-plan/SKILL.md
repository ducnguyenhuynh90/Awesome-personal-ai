---
name: onboarding-plan
description: Builds a 30/60/90 onboarding plan with milestones and owners. Use when a new hire, new team member or contractor needs a 30/60/90 day onboarding plan.
metadata:
  department: people
  tags:
  - onboarding
  - 30 60 90
  - new hire
  - ramp up
  - first week
  - induction
  examples:
  - Make a 30/60/90 plan for the new CRM engineer
  - First-week onboarding checklist for support agents
  writes_to:
  - outbox/
---

# onboarding-plan

Builds a 30/60/90 onboarding plan with milestones and owners.

## Steps

1. Outcomes the person must hit by day 30/60/90.
2. Week 1 checklist: access, people to meet, docs to read (links).
3. Milestones with an owner and a check-in date.

## Output

Day 30/60/90 outcomes · Week-1 checklist · Check-ins. Saved to outbox/.

## Quality checks

- Outcomes are measurable.
- Access requests listed.
