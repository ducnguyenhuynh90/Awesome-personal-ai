---
name: incident-postmortem
description: 'Blameless postmortem: impact, timeline, root cause, actions. Use when an outage, incident or serious bug happened and needs a blameless postmortem or timeline.'
metadata:
  department: engineering
  tags:
  - incident
  - outage
  - postmortem
  - post-mortem
  - downtime
  - root cause
  - rca
  - bug
  examples:
  - Write the postmortem for yesterday's deposit outage
  - Timeline of the login incident from these logs
  writes_to:
  - outbox/
---

# incident-postmortem

Blameless postmortem: impact, timeline, root cause, actions.

## Steps

1. Impact: who, how many, how long, money/KPI effect (aggregates).
2. Timeline from logs/messages with timestamps.
3. Root cause via 5 whys; contributing factors.
4. Actions: prevent, detect, mitigate — each with owner and date.
5. Blameless: systems and processes, not people.

## Output

Impact · Timeline · Root cause · Actions (owner, date). Saved to outbox/.

## Quality checks

- Blameless.
- Every action has an owner.

## Pitfalls (learned)

- Naming individuals as the cause.
